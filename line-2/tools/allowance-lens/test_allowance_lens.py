"""Offline regression tests; fixture is a real Ethereum observation.

Mutated copies exercise edge cases and are never described as chain evidence.
All addresses and hashes originate in the real fixture; no wallet is involved.
"""

import contextlib
import copy
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import allowance_lens as lens

HERE = Path(__file__).resolve().parent
OBSERVATION = json.loads((HERE / 'observation.json').read_text())


def encoded(n):
    return '0x' + format(n, '064x')


class ReplayRPC:
    endpoint = lens.PUBLIC_RPC

    def __init__(self):
        self.calls = []
        self.final_reads = 0
        self.reorg = False
        self.chain = '0x1'
        self.empty = False

    def call(self, method, params):
        self.calls.append((method, copy.deepcopy(params)))
        if method == 'eth_chainId':
            return self.chain
        if method == 'eth_getBlockByNumber':
            if params[0] in ('finalized', OBSERVATION['block']['number']):
                self.final_reads += 1
                result = copy.deepcopy(OBSERVATION['block'])
                if self.reorg and self.final_reads > 1:
                    result['hash'] = next(iter(OBSERVATION['log_headers'].values()))['hash']
                return result
            return copy.deepcopy(OBSERVATION['log_headers'][params[0]])
        if method == 'eth_getLogs':
            query = params[0]
            assert query['address'] == lens.TOKENS['ZTO']
            first, last = (int(query[k], 16) for k in ('fromBlock', 'toBlock'))
            assert last - first < 250
            return [] if self.empty else [copy.deepcopy(log) for log in reversed(OBSERVATION['logs'])
                    if first <= int(log['blockNumber'], 16) <= last
                    and (len(query['topics']) == 1 or log['topics'][1] == query['topics'][1])]
        if method == 'eth_call':
            assert params[0]['to'] == lens.TOKENS['ZTO']
            assert params[1] == {'blockHash': OBSERVATION['block']['hash'], 'requireCanonical': True}
            data = params[0]['data']
            if data == '0x313ce567':
                return OBSERVATION['raw']['decimals']
            for item in OBSERVATION['raw']['balances'] + OBSERVATION['raw']['allowances']:
                if item['data'] == data:
                    return item['result']
            raise AssertionError('unexpected calldata')
        raise AssertionError('unexpected RPC method')


class AllowanceLensTests(unittest.TestCase):
    def setUp(self):
        self.obs = copy.deepcopy(OBSERVATION)

    def test_real_observation_matches_recorded_report(self):
        expected = json.loads((HERE / 'example-report.json').read_text())
        self.assertEqual(lens.report(self.obs), expected)
        self.assertEqual((expected['pair_count'], expected['active_pair_count']), (19, 3))
        self.assertEqual(expected['approval_event_count'], 27)

    def test_event_amount_is_not_used_as_current_allowance(self):
        report = lens.report(self.obs)
        changed = [r for r in report['pairs'] if r['last_observed_approval']['differs_from_current_allowance']]
        self.assertEqual(len(changed), 15)
        self.assertTrue(any(r['allowance_raw'] == '0' and r['last_observed_approval']['amount_raw'] != '0'
                            for r in changed))

    def test_zero_balance_is_not_revocation(self):
        rows = lens.report(self.obs)['pairs']
        dormant = [r for r in rows if r['status'] == 'active_zero_balance']
        self.assertEqual(len(dormant), 2)
        self.assertTrue(all(int(r['allowance_raw']) > 0 and r['balance_raw'] == '0' for r in dormant))

    def test_owner_total_does_not_double_count_balance(self):
        # Give every discovered pair max allowance, without changing real addresses.
        for item in self.obs['raw']['allowances']:
            item['result'] = encoded(lens.MAX_UINT)
        result = lens.report(self.obs)
        self.assertTrue(all(r['max_uint256'] for r in result['pairs']))
        for row in result['owners']:
            self.assertEqual(row['balance_raw'], row['combined_spendable_upper_bound_raw'])
        owners = [p['owner'] for p in result['pairs']]
        self.assertLess(len(set(owners)), len(owners))

    def test_finite_allowance_caps_spendable_amount(self):
        for item in self.obs['raw']['allowances']:
            item['result'] = encoded(1)
        for row in lens.report(self.obs)['pairs']:
            self.assertEqual(int(row['spendable_upper_bound_raw']), min(1, int(row['balance_raw'])))

    def test_shuffled_events_are_order_independent(self):
        expected = lens.report(self.obs)
        self.obs['logs'].reverse()
        self.assertEqual(lens.report(self.obs), expected)

    def test_duplicate_removed_and_out_of_window_logs_fail(self):
        for kind in ('duplicate', 'removed', 'out_of_window', 'wrong_token', 'address_padding'):
            with self.subTest(kind=kind):
                obs = copy.deepcopy(self.obs)
                if kind == 'duplicate':
                    obs['logs'].append(copy.deepcopy(obs['logs'][0]))
                elif kind == 'removed':
                    obs['logs'][0]['removed'] = True
                elif kind == 'out_of_window':
                    obs['logs'][0]['blockNumber'] = hex(obs['query']['from_block'] - 1)
                elif kind == 'wrong_token':
                    obs['logs'][0]['address'] = lens.TOKENS['IMD']
                else:
                    obs['logs'][0]['topics'][1] = '0x1' + obs['logs'][0]['topics'][1][3:]
                with self.assertRaises(ValueError):
                    lens.report(obs)

    def test_missing_or_duplicate_state_results_fail(self):
        for group in ('allowances', 'balances'):
            for mutation in ('missing', 'duplicate', 'calldata', 'short_result'):
                with self.subTest(group=group, mutation=mutation):
                    obs = copy.deepcopy(self.obs)
                    values = obs['raw'][group]
                    if mutation == 'missing':
                        values.pop()
                    elif mutation == 'duplicate':
                        values.append(copy.deepcopy(values[0]))
                    elif mutation == 'calldata':
                        values[0]['data'] = '0x'
                    else:
                        values[0]['result'] = '0x01'
                    with self.assertRaises(ValueError):
                        lens.report(obs)

    def test_wrong_chain_token_and_decimals_fail(self):
        for mutation in ('chain', 'token', 'decimals'):
            obs = copy.deepcopy(self.obs)
            if mutation == 'chain':
                obs['chain_id'] = 8453
            elif mutation == 'token':
                obs['token_address'] = lens.TOKENS['IMD']
            else:
                obs['raw']['decimals'] = encoded(256)
            with self.assertRaises(ValueError):
                lens.report(obs)

    def test_log_header_mismatch_fails(self):
        first = self.obs['logs'][0]
        self.obs['log_headers'][first['blockNumber']]['hash'] = self.obs['block']['hash']
        with self.assertRaisesRegex(ValueError, 'log block hash mismatch'):
            lens.report(self.obs)

    def test_capture_replays_real_responses_with_hash_pinning(self):
        rpc = ReplayRPC()
        captured = lens.capture(rpc)
        self.assertEqual(lens.report(captured), lens.report(self.obs))
        self.assertEqual(sum(m == 'eth_getLogs' for m, _ in rpc.calls), 6)
        self.assertTrue(all(m in lens.RPC.METHODS for m, _ in rpc.calls))

    def test_reorg_is_rejected(self):
        rpc = ReplayRPC()
        rpc.reorg = True
        with self.assertRaisesRegex(ValueError, 'block changed'):
            lens.capture(rpc)

    def test_wrong_chain_stops_before_state_queries(self):
        rpc = ReplayRPC()
        rpc.chain = '0x2105'
        with self.assertRaisesRegex(ValueError, 'Ethereum chain 1'):
            lens.capture(rpc)
        self.assertEqual(len(rpc.calls), 1)

    def test_explicit_pairs_do_not_scan_logs(self):
        pair = self.obs['raw']['allowances'][0]
        rpc = ReplayRPC()
        result = lens.report(lens.capture(rpc, owner=pair['owner'], spenders=[pair['spender']]))
        self.assertEqual(result['pair_count'], 1)
        self.assertIsNone(result['pairs'][0]['last_observed_approval'])
        self.assertEqual(result['pairs'][0]['allowance_raw'], str(lens.word(pair['result'])))
        self.assertFalse(any(m == 'eth_getLogs' for m, _ in rpc.calls))
        self.assertFalse(result['complete_wallet_audit'])

    def test_owner_filter_limits_discovery(self):
        owner = self.obs['raw']['allowances'][0]['owner']
        result = lens.report(lens.capture(ReplayRPC(), owner=owner))
        self.assertGreater(result['pair_count'], 0)
        self.assertTrue(all(r['owner'] == owner for r in result['pairs']))

    def test_empty_window_does_not_claim_wallet_is_safe(self):
        rpc = ReplayRPC()
        rpc.empty = True
        result = lens.report(lens.capture(rpc))
        self.assertEqual(result['pairs'], [])
        self.assertFalse(result['complete_wallet_audit'])

    def test_query_limits_are_enforced_before_network(self):
        for window in (0, 2001, True):
            rpc = ReplayRPC()
            with self.assertRaises(ValueError):
                lens.capture(rpc, window=window)
            self.assertEqual(rpc.calls, [])
        with self.assertRaises(ValueError):
            lens.capture(ReplayRPC(), spenders=[self.obs['raw']['allowances'][0]['spender']])

    def test_integer_formatting_never_uses_float(self):
        self.assertEqual(lens.units(1, 18), '0.000000000000000001')
        self.assertEqual(lens.units(123450000, 6), '123.45')
        self.assertEqual(lens.units(lens.MAX_UINT, 0), str(lens.MAX_UINT))
        self.assertEqual(lens.units(0, 18), '0')

    def test_transport_rejects_send_methods_before_opening(self):
        rpc = lens.RPC(lens.PUBLIC_RPC)
        with patch.object(rpc.opener, 'open', side_effect=AssertionError('network forbidden')):
            with self.assertRaises(ValueError):
                rpc.call('eth_sendRawTransaction', [])
        with self.assertRaises(ValueError):
            lens.RPC('http://localhost:1')

    def test_offline_cli_never_constructs_rpc(self):
        output = io.StringIO()
        with patch.object(lens, 'RPC', side_effect=AssertionError('RPC forbidden')):
            with contextlib.redirect_stdout(output):
                status = lens.main(['--snapshot', str(HERE / 'observation.json')])
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(output.getvalue()), lens.report(self.obs))

    def test_offline_cli_rejects_live_query_options(self):
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            status = lens.main(['--token', 'IMD'])
        self.assertEqual(status, 1)
        self.assertIn('require --live', json.loads(errors.getvalue())['error'])

    def test_workspace_boundary_rejected_without_reading(self):
        with self.assertRaisesRegex(ValueError, 'current workspace'):
            lens.workspace_path(Path.cwd().parent / 'outside.json')


if __name__ == '__main__':
    unittest.main()
