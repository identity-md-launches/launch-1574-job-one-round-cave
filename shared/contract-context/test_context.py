"""Offline real-observation checks and explicitly synthetic transport branches."""
import copy
import contextlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import context as c

HERE = Path(__file__).resolve().parent
IDENTITY = json.loads((HERE / 'code-observation.json').read_text())
REHEARSAL = json.loads((HERE / 'call-observation.json').read_text())


class SyntheticRPC:
    """Recombine recorded responses for branch tests, never claim a live capture."""
    endpoint = c.call.ENDPOINTS[0]

    def __init__(self):
        self.calls = []
        self.header_reads = 0
        self.code_reads = 0
        self.change_header = False
        self.change_code = False
        self.outcome = copy.deepcopy(REHEARSAL['outcome'])

    def call(self, method, params):
        self.calls.append((method, copy.deepcopy(params)))
        if method == 'eth_chainId':
            return '0x1'
        if method == 'eth_getBlockByNumber':
            self.header_reads += 1
            result = copy.deepcopy(REHEARSAL['block'])
            if self.change_header and self.header_reads > 1:
                result['hash'] = IDENTITY['block']['hash']
            return result
        if method == 'eth_getCode':
            self.code_reads += 1
            return '0x6000' if self.change_code and self.code_reads > 1 else IDENTITY['nodes'][0]['code']
        if method == 'eth_getStorageAt':
            slot = next(k for k, value in c.code.SLOTS.items() if value == params[1])
            return IDENTITY['nodes'][0]['storage'][slot]
        if method == 'eth_call':
            if 'error' in self.outcome:
                raise c.call.RPCError(self.outcome['error'])
            return self.outcome['result']
        raise AssertionError(method)


class ContextTests(unittest.TestCase):
    def test_real_observations_are_not_same_block(self):
        result = c.compare(IDENTITY, REHEARSAL)
        self.assertTrue(result['same_target'])
        self.assertFalse(result['same_block'])
        self.assertEqual(c.exit_status(result), 2)
        self.assertEqual(c.code.quantity(REHEARSAL['block']['number']) -
                         c.code.quantity(IDENTITY['block']['number']), 32)

    def test_default_demo_never_constructs_rpc(self):
        with patch.object(c, 'RPC', side_effect=AssertionError('network forbidden')):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(c.main([]), 2)
        self.assertFalse(json.loads(output.getvalue())['coherent'])

    def test_collectors_share_one_finalized_selection_and_hash(self):
        rpc = SyntheticRPC()
        bundle = c.capture(rpc, REHEARSAL['call'])
        self.assertTrue(c.verify(bundle)['coherent'])
        self.assertEqual(sum(m == 'eth_getBlockByNumber' and p[0] == 'finalized'
                             for m, p in rpc.calls), 1)
        pin = {'blockHash': REHEARSAL['block']['hash'], 'requireCanonical': True}
        for method, params in rpc.calls:
            if method in ('eth_getCode', 'eth_getStorageAt', 'eth_call'):
                self.assertEqual(params[-1], pin)
        self.assertEqual(rpc.code_reads, 2)

    def test_changed_header_is_rejected(self):
        rpc = SyntheticRPC()
        rpc.change_header = True
        with self.assertRaisesRegex(ValueError, 'header changed'):
            c.capture(rpc, REHEARSAL['call'])

    def test_conflicting_runtime_is_rejected(self):
        rpc = SyntheticRPC()
        rpc.change_code = True
        with self.assertRaisesRegex(ValueError, 'conflicting runtime'):
            c.capture(rpc, REHEARSAL['call'])

    def test_number_and_hash_must_both_agree(self):
        bundle = c.capture(SyntheticRPC(), REHEARSAL['call'])
        for key in ('number', 'hash'):
            modified = copy.deepcopy(bundle)
            modified['code']['block'][key] = IDENTITY['block'][key]
            with self.assertRaisesRegex(ValueError, 'mismatched block'):
                c.verify(modified)

    def test_target_mismatch_is_rejected(self):
        bundle = c.capture(SyntheticRPC(), REHEARSAL['call'])
        bundle['rehearsal']['call']['to'] = c.call.TOKENS['IMD']
        with self.assertRaisesRegex(ValueError, 'mismatched block or target'):
            c.verify(bundle)

    def test_runtime_tampering_is_rejected(self):
        bundle = c.capture(SyntheticRPC(), REHEARSAL['call'])
        bundle['code']['nodes'][0]['code'] = '0x6000'
        with self.assertRaises(ValueError):
            c.verify(bundle)

    def test_revert_is_preserved_in_coherent_context(self):
        rpc = SyntheticRPC()
        rpc.outcome = {'error': {'code': 3, 'message': 'execution reverted'}}
        result = c.verify(c.capture(rpc, REHEARSAL['call']))
        self.assertTrue(result['coherent'])
        self.assertEqual(c.exit_status(result), 1)

    def test_false_and_malformed_return_are_not_success(self):
        for value, expected in [(0, 1), (1, 0), (2, 2)]:
            rpc = SyntheticRPC()
            rpc.outcome = {'result': '0x' + format(value, '064x')}
            self.assertEqual(c.exit_status(c.verify(c.capture(rpc, REHEARSAL['call'], 'bool'))), expected)

    def test_incomplete_custom_call_fails_before_network(self):
        with patch.object(c, 'RPC', side_effect=AssertionError('network forbidden')):
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(c.main(['live', '--to', c.call.TOKENS['ZTO']]), 2)

    def test_workspace_boundary_before_read(self):
        with self.assertRaisesRegex(ValueError, 'workspace'):
            c.read_json(Path.cwd().parent / 'outside.json')

    def test_source_mismatch_is_rejected(self):
        bundle = c.capture(SyntheticRPC(), REHEARSAL['call'])
        bundle['transport_source'] = c.call.ENDPOINTS[1]
        with self.assertRaisesRegex(ValueError, 'source mismatch'):
            c.verify(bundle)

    def test_transport_guard_remains_read_only(self):
        rpc = c.RPC(c.call.ENDPOINTS[0])
        with patch.object(rpc.opener, 'open', side_effect=AssertionError('network forbidden')):
            with self.assertRaisesRegex(ValueError, 'allowlisted'):
                rpc.call('eth_sendRawTransaction', [])


if __name__ == '__main__':
    unittest.main()
