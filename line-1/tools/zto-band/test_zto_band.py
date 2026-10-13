"""Offline tests, including recorded results from the real deployed quoter."""

import copy
import contextlib
from fractions import Fraction
import io
import json
from pathlib import Path
import random
import unittest
from unittest.mock import patch

import zto_band as z
from keccak import keccak256, selector
from math_core import (Q96, amount0, amount1, capacity, ceil_div, interior_target,
                       sqrt_at_tick, swap_step, total_fee)

HERE = Path(__file__).resolve().parent


class BandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.observation = json.loads((HERE / 'observation.json').read_text())

    def test_keccak_known_vectors(self):
        self.assertEqual(keccak256(b'').hex(), 'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470')
        self.assertEqual(keccak256(b'abc').hex(), '4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45')
        self.assertEqual(selector('transfer(address,uint256)'), '0xa9059cbb')
        self.assertEqual(selector('getSlot0(bytes32)'), '0xc815641c')

    def test_tick_extremes(self):
        self.assertEqual(sqrt_at_tick(0), Q96)
        self.assertEqual(sqrt_at_tick(-887272), 4295128739)
        self.assertEqual(sqrt_at_tick(887272), 1461446703485210103287273052203988822378723970342)
        self.assertEqual(sqrt_at_tick(1), 79232123823359799118286999568)
        with self.assertRaises(ValueError):
            sqrt_at_tick(887273)

    def test_negative_tick_floor(self):
        self.assertEqual(interior_target(-1, 60, True), (sqrt_at_tick(-60)+1, -60))
        self.assertEqual(interior_target(-1, 60, False), (Q96-1, 0))

    def test_fees_are_directional(self):
        packed = 1000 | (500 << 12)
        self.assertEqual(total_fee(packed, 12500, True), 13488)
        self.assertEqual(total_fee(packed, 12500, False), 12994)
        with self.assertRaises(ValueError):
            total_fee(1001, 12500, True)

    def test_rational_delta_rounding(self):
        rng = random.Random(737)
        for _ in range(150):
            a = sqrt_at_tick(rng.randrange(-700000, 700000))
            b = a + rng.randrange(1, 10**20)
            liquidity = rng.randrange(1, 1 << 128)
            for fn, exact in ((amount0, Fraction(liquidity * Q96 * (b-a), a*b)),
                              (amount1, Fraction(liquidity * (b-a), Q96))):
                self.assertEqual(fn(a, b, liquidity), exact.numerator // exact.denominator)
                self.assertEqual(fn(a, b, liquidity, True), ceil_div(exact.numerator, exact.denominator))

    def test_pool_identity_and_real_decimals(self):
        state = z.decode(self.observation)
        self.assertEqual(state['decimals'], [18, 18])
        self.assertEqual(state['tick'], 110768)
        self.assertEqual(state['hook'], '0x784ff9a3ac5d88a30bfff6f7f2a270161fbe6000')

    def test_real_quoter_regressions(self):
        evidence = json.loads((HERE / 'quoter-check.json').read_text())
        self.assertEqual(evidence['block'], self.observation['block'])
        self.assertEqual(len(evidence['results']), 8)
        for case in evidence['results']:
            self.assertTrue(case['matches'])
            result = z.report(self.observation, case['input_token'], case['input'])
            actual = str(z.words(case['raw_result'], 2)[0])
            self.assertEqual(result['estimate']['output_raw'], actual)

    def test_interval_cap_and_refusal(self):
        for token in ('ZTO', 'IMD'):
            result = z.report(self.observation, token)
            cap = int(result['interval_input_cap_raw'])
            self.assertEqual(result['status'], 'estimated')
            self.assertEqual(result['estimate']['sqrt_price_after_x96'], result['sqrt_price_limit_x96'])
            self.assertEqual(result['estimate']['input_unspent_raw'], '0')
            outside = z.report(self.observation, token, z.units(cap+1, 18))
            self.assertEqual(outside['status'], 'outside_interval')
            self.assertNotIn('estimate', outside)

    def test_monotonic_and_conservation(self):
        state = z.decode(self.observation)
        for direction in (True, False):
            target, _ = interior_target(state['tick'], 60, direction)
            cap = capacity(state['price'], target, state['liquidity'], 12500, direction)
            previous = 0
            for amount in [1, 2, 100, cap//1000, cap//2, cap, cap+100]:
                step = swap_step(state['price'], target, state['liquidity'], 12500, amount, direction)
                self.assertGreaterEqual(int(step['output_raw']), previous)
                previous = int(step['output_raw'])
                self.assertEqual(int(step['input_consumed_raw']) + int(step['input_unspent_raw']), amount)
                self.assertEqual(int(step['input_to_pool_raw']) + int(step['fee_raw']), int(step['input_consumed_raw']))
                nxt = int(step['sqrt_price_after_x96'])
                self.assertTrue(min(target, state['price']) <= nxt <= max(target, state['price']))

    def test_zero_liquidity(self):
        obs = copy.deepcopy(self.observation)
        obs['raw']['liquidity'] = '0x' + z.word(0).hex()
        self.assertEqual(z.report(obs)['status'], 'no_interval_capacity')

    def test_exact_boundary_safely_refused_in_one_direction(self):
        obs = copy.deepcopy(self.observation)
        obs['raw']['slot0'] = '0x' + b''.join(z.word(x) for x in (sqrt_at_tick(110760), 110760, 0, 12500)).hex()
        self.assertEqual(z.report(obs, 'IMD')['status'], 'no_interval_capacity')
        self.assertEqual(z.report(obs, 'ZTO')['status'], 'estimated')
        # At a just-crossed downward boundary the stored tick is boundary - 1.
        obs['raw']['slot0'] = '0x' + b''.join(z.word(x) for x in (sqrt_at_tick(110760), 110759, 0, 12500)).hex()
        self.assertEqual(z.report(obs, 'ZTO')['status'], 'no_interval_capacity')
        self.assertEqual(z.report(obs, 'IMD')['status'], 'estimated')

    def test_reject_corrupted_observation(self):
        mutations = [lambda o: o.update(chain_id='0x2105'),
                     lambda o: o['initialize'].update(removed=True),
                     lambda o: o['initialize']['topics'].__setitem__(2, o['initialize']['topics'][3]),
                     lambda o: o['raw'].update(slot0='0x'),
                     lambda o: o['raw'].update(imd_decimals='0x' + z.word(37).hex()),
                     lambda o: o['raw'].update(state_view_manager='0x' + z.word(int(z.ZTO,16)).hex())]
        for mutate in mutations:
            obs = copy.deepcopy(self.observation)
            mutate(obs)
            with self.assertRaises(ValueError):
                z.decode(obs)

    def test_amount_precision(self):
        self.assertEqual(z.parse_amount('1.000000000000000001',18),10**18+1)
        for value in ('-1', '0', '1e18', 'NaN', '0.0000000000000000001', '.1'):
            with self.assertRaises(ValueError):
                z.parse_amount(value,18)
        self.assertEqual(z.units(10**18,18), '1')

    def test_offline_cli_does_not_construct_rpc(self):
        with patch.object(z, 'RPC', side_effect=AssertionError('network forbidden')):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                code = z.main(['--snapshot', str(HERE/'observation.json'), '--amount','1'])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue())['estimate']['output_raw'], '15282142320759')

    def test_rpc_allowlist_and_credential_rejection(self):
        with self.assertRaises(ValueError):
            z.RPC('https://username:password@example.com')
        with self.assertRaises(ValueError):
            z.RPC(z.PUBLIC_RPC).call('eth_sendRawTransaction', [])

    def test_live_capture_uses_one_block_hash(self):
        obs = self.observation
        seen = []
        responses = [obs['chain_id'], obs['block'], {'hash': obs['initialize']['blockHash']},
                     [obs['initialize']]] + list(obs['raw'].values()) + [obs['block']]
        class FakeRPC:
            def __init__(self, endpoint):
                pass
            def call(self, method, params):
                seen.append((method, params))
                return responses[len(seen)-1]
        with patch.object(z, 'RPC', FakeRPC):
            captured = z.capture(z.PUBLIC_RPC, 'finalized')
        self.assertEqual(captured, obs)
        calls = [params for method, params in seen if method == 'eth_call']
        self.assertEqual(len(calls), 5)
        for params in calls:
            self.assertEqual(params[1], {'blockHash': obs['block']['hash'], 'requireCanonical': True})
        responses[-1] = dict(obs['block'], hash='changed')
        seen.clear()
        with patch.object(z, 'RPC', FakeRPC), self.assertRaisesRegex(ValueError, 'changed during capture'):
            z.capture(z.PUBLIC_RPC, 'finalized')


if __name__ == '__main__':
    unittest.main()
