"""Offline synthetic RPC branches; live observations are tested separately."""
import contextlib
import copy
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import rehearse as r

BLOCK = {'number': '0x123', 'hash': '0x' + 'ab' * 32, 'timestamp': '0x456'}
TX = {'to': r.TOKENS['ZTO'], 'data': '0x18160ddd', 'value': '0x0'}


def word(number):
    return '0x' + format(number, '064x')


class FakeRPC:
    endpoint = r.ENDPOINTS[0]

    def __init__(self, result=None, error=None, chain='0x1', code='0x6000', changed=False):
        self.result = word(10) if result is None else result
        self.error, self.chain, self.code, self.changed = error, chain, code, changed
        self.calls = []

    def call(self, method, params):
        self.calls.append((method, copy.deepcopy(params)))
        if method == 'eth_chainId':
            return self.chain
        if method == 'eth_getBlockByNumber':
            block = dict(BLOCK)
            if self.changed and params[0] != 'finalized':
                block['hash'] = '0x' + 'cd' * 32
            return block
        if method == 'eth_getCode':
            return self.code
        if method == 'eth_call':
            if self.error:
                raise r.RPCError(self.error)
            return self.result
        raise AssertionError('Unexpected RPC method: ' + method)


class RehearsalTests(unittest.TestCase):
    def test_hash_pinned_reads_and_postcheck(self):
        rpc = FakeRPC()
        observed = r.capture(rpc, TX, 'uint256')
        self.assertEqual(r.report(observed)['result']['uint256'], '10')
        pin = {'blockHash': BLOCK['hash'], 'requireCanonical': True}
        self.assertEqual(rpc.calls[2], ('eth_getCode', [TX['to'], pin]))
        self.assertEqual(rpc.calls[3], ('eth_call', [TX, pin]))
        self.assertEqual(rpc.calls[4], ('eth_getBlockByNumber', [BLOCK['number'], False]))

    def test_wrong_chain_stops_before_call(self):
        rpc = FakeRPC(chain='0xa')
        with self.assertRaisesRegex(ValueError, 'mainnet'):
            r.capture(rpc, TX, 'uint256')
        self.assertEqual(len(rpc.calls), 1)

    def test_missing_code_stops_before_call(self):
        rpc = FakeRPC(code='0x')
        with self.assertRaisesRegex(ValueError, 'no code'):
            r.capture(rpc, TX, 'uint256')
        self.assertNotIn('eth_call', [m for m, _ in rpc.calls])

    def test_block_change_discards_observation(self):
        with self.assertRaisesRegex(ValueError, 'block changed'):
            r.capture(FakeRPC(changed=True), TX, 'uint256')

    def test_false_is_not_success(self):
        self.assertEqual(r.interpret({'result': word(0)}, 'bool')['status'], 'returned_false')
        self.assertEqual(r.interpret({'result': word(1)}, 'bool')['status'], 'returned_true')
        self.assertEqual(r.interpret({'result': word(2)}, 'bool')['status'], 'unexpected_return')

    def test_empty_return_is_only_success_for_raw(self):
        self.assertEqual(r.interpret({'result': '0x'}, 'raw')['status'], 'returned')
        self.assertEqual(r.interpret({'result': '0x'}, 'bool')['status'], 'unexpected_return')

    def test_error_string(self):
        reason = b'not enough tokens'
        raw = '0x08c379a0' + word(32)[2:] + word(len(reason))[2:] + reason.hex().ljust(64, '0')
        error = {'code': 3, 'message': 'execution reverted', 'data': raw}
        report = r.report(r.capture(FakeRPC(error=error), TX, 'raw'))
        self.assertEqual(report['result']['status'], 'reverted')
        self.assertEqual(report['result']['revert']['reason'], reason.decode())

    def test_panic_and_custom_error(self):
        self.assertEqual(r.decode_revert('0x4e487b71' + word(0x11)[2:])['code'], '0x11')
        self.assertEqual(r.decode_revert('0x11223344' + word(7)[2:])['kind'], 'custom_or_unknown')

    def test_truncated_revert_not_invented(self):
        self.assertEqual(r.decode_revert('0x08c379a0' + word(32)[2:])['kind'], 'custom_or_unknown')
        self.assertEqual(r.decode_revert('0x')['kind'], 'empty_or_truncated')

    def test_rpc_failure_is_inconclusive(self):
        result = r.interpret({'error': {'code': -32000, 'message': 'missing trie node'}}, 'raw')
        self.assertEqual(result['status'], 'inconclusive')

    def test_sender_and_amount_required_for_transfer(self):
        # Public addresses are encoding test data, not claimed token owners.
        tx = r.transfer('ZTO', r.TOKENS['IMD'], r.TOKENS['ZTO'], '123')
        self.assertEqual(tx['data'], '0xa9059cbb' + r.TOKENS['ZTO'][2:].rjust(64, '0') + word(123)[2:])
        self.assertEqual(tx['from'], r.TOKENS['IMD'])
        for value in ('-1', '1.5', '01', str(2**256)):
            with self.subTest(value=value), self.assertRaises(ValueError):
                r.amount(value)

    def test_custom_call_cannot_invent_sender(self):
        with self.assertRaisesRegex(ValueError, 'explicit sender'):
            r.transaction(dict(TX, data='0xa9059cbb'))
        self.assertEqual(r.transaction(TX), TX)

    def test_reject_bad_inputs(self):
        for value in ('0x1', '0xgg', '', '1234'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                r.data(value)
        with self.assertRaises(ValueError):
            r.address('0x' + '00' * 20)
        with self.assertRaises(ValueError):
            r.transaction(dict(TX, gas='0x10'))

    def test_large_runtime_code_and_bound(self):
        # IMD's real runtime exposed the initial overly small 16 KiB limit.
        observed = r.capture(FakeRPC(code='0x' + '60' * 24576), TX, 'uint256')
        self.assertTrue(observed['code_present'])
        with self.assertRaisesRegex(ValueError, '32 KiB'):
            r.data('0x' + '60' * 32769)

    def test_read_only_allowlist(self):
        rpc = r.RPC(r.ENDPOINTS[0])
        with self.assertRaisesRegex(ValueError, 'allowlisted'):
            rpc.call('eth_sendRawTransaction', [])
        with self.assertRaises(ValueError):
            r.RPC('https://unapproved.invalid')

    def test_workspace_escape(self):
        with self.assertRaisesRegex(ValueError, 'workspace'):
            r.workspace_path('../outside-observation.json')

    def test_bad_observation(self):
        obs = r.capture(FakeRPC(), TX, 'uint256')
        for key, value in [('chain_id', True), ('code_present', False), ('source', 'other'),
                           ('returns', 'guess')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                r.report(dict(obs, **{key: value}))

    def test_rpc_envelope_validation(self):
        rpc = r.RPC(r.ENDPOINTS[0])
        for body in [{'jsonrpc': '2.0', 'id': 9, 'result': '0x1'},
                     {'jsonrpc': '2.0', 'id': 1, 'result': '0x1', 'error': {}},
                     {'jsonrpc': '2.0', 'id': True, 'result': '0x1'}]:
            rpc.counter = 0
            with patch.object(rpc.opener, 'open', return_value=io.BytesIO(json.dumps(body).encode())):
                with self.assertRaises(ValueError):
                    rpc.call('eth_chainId', [])

    def test_cli_exit_codes_without_network(self):
        for outcome, returns, expected in [({'result': word(1)}, 'bool', 0),
                                           ({'result': word(0)}, 'bool', 1),
                                           ({'result': '0x'}, 'bool', 2),
                                           ({'error': {'code': 3, 'message': 'execution reverted'}}, 'raw', 1)]:
            obs = r.capture(FakeRPC(), TX, returns)
            obs['outcome'] = outcome
            with patch.object(r, 'capture', return_value=obs), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(r.main(['demo']), expected)

    def test_saved_real_observation_offline(self):
        observation = json.loads(Path(__file__).with_name('zto-observation.json').read_text())
        result = r.report(observation)
        self.assertEqual(result['call']['to'], r.TOKENS['ZTO'])
        self.assertEqual(result['result']['status'], 'returned')
        self.assertGreater(int(result['result']['uint256']), 0)


if __name__ == '__main__':
    unittest.main()
