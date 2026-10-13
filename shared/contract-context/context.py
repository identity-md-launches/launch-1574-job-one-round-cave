#!/usr/bin/env python3
"""Join runtime identity and call rehearsal at one Ethereum block; reads only."""
import argparse
import json
from pathlib import Path
import sys

import code_lens as code
import rehearse as call

SCHEMA = 'contract-context-v1'
LIMIT = 98_000


class RPC(call.RPC):
    """Reuse Call Rehearsal's transport; add Code Lens's storage read."""
    METHODS = call.RPC.METHODS | {'eth_getStorageAt'}


class PinnedSession:
    """Make both original collectors resolve finalized to the same real header."""
    def __init__(self, rpc):
        self.rpc = rpc
        self.endpoint = rpc.endpoint
        call.require(rpc.call('eth_chainId', []) == '0x1', 'expected Ethereum mainnet')
        self.block = call.header(rpc.call('eth_getBlockByNumber', ['finalized', False]))
        self.pin = {'blockHash': self.block['hash'], 'requireCanonical': True}
        self.runtimes = {}

    def call(self, method, params):
        call.require(method in RPC.METHODS, 'method is not read-only allowlisted')
        if method == 'eth_getBlockByNumber':
            call.require(params[0] in ('finalized', self.block['number']), 'unexpected block request')
            result = self.rpc.call(method, [self.block['number'], False])
            call.require(call.header(result) == self.block, 'pinned header changed between collectors')
            return result
        if method in ('eth_getCode', 'eth_getStorageAt', 'eth_call'):
            call.require(params[-1] == self.pin, 'collector escaped the pinned block')
        result = self.rpc.call(method, params)
        if method == 'eth_getCode':
            target, runtime = call.address(params[0]), call.data(result)
            call.require(target not in self.runtimes or self.runtimes[target] == runtime,
                         'provider returned conflicting runtime at the same block')
            self.runtimes[target] = runtime
        return result


def compare(identity, rehearsal):
    """Validate each source, then assess linkage; never relabel a mismatched block."""
    code.verify(identity)
    result = call.report(rehearsal)
    same_target = identity['target'].lower() == result['call']['to']
    same_number = code.quantity(identity['block']['number']) == result['block_number']
    same_hash = identity['block']['hash'].lower() == result['block_hash']
    same_block = same_number and same_hash
    coherent = same_target and same_block
    return {
        'schema': 'contract-context-assessment-v1',
        'coherent': coherent,
        'status': 'same_block_context' if coherent else 'context_mismatch',
        'same_target': same_target, 'same_block': same_block,
        'code_block': identity['block'],
        'call_block': rehearsal['block'],
        'target': result['call']['to'],
        'code_target': identity['target'],
        'root_code_hash': identity['nodes'][0]['code_hash'],
        'candidate_effective_address': identity['effective_address'],
        'candidate_effective_code_hash': identity['effective_code_hash'],
        'proxy_signals': [node['kind'] for node in identity['nodes']],
        'call': result['call'], 'execution': result['result'],
        'limits': [
            'Offline checks establish internal consistency, not chain authenticity.',
            'A shared block and target link evidence; they do not certify contract safety.',
            'Proxy slots identify candidates, not proof of actual execution routing.',
            'No receipt, gas estimate, state diff or guarantee of future execution.',
            'Source observations remain historical; no keys or transactions are involved.',
        ],
    }


def capture(rpc, tx, returns='uint256', expected=None):
    tx = call.transaction(tx)
    call.require(returns in ('raw', 'uint256', 'bool'), 'unsupported return interpretation')
    if expected is not None:
        expected = code.fixed_hex(expected, 32)
    session = PinnedSession(rpc)
    identity = code.collect(session, tx['to'], expected)
    rehearsal = call.capture(session, tx, returns)
    result = compare(identity, rehearsal)
    call.require(result['coherent'], 'collectors did not produce coherent context')
    return {'schema': SCHEMA, 'transport_source': rpc.endpoint,
            'code': identity, 'rehearsal': rehearsal}


def verify(bundle):
    call.require(isinstance(bundle, dict) and bundle.get('schema') == SCHEMA,
                 'unsupported context schema')
    call.require(bundle['transport_source'] in call.ENDPOINTS, 'unsupported transport source')
    call.require(bundle['rehearsal']['source'] == bundle['transport_source'], 'source mismatch')
    result = compare(bundle['code'], bundle['rehearsal'])
    call.require(result['coherent'], 'context bundle has mismatched block or target')
    return result


def read_json(filename):
    with call.workspace_path(filename).open('rb') as handle:
        raw = handle.read(LIMIT + 1)
    call.require(len(raw) <= LIMIT, 'input exceeds 98000 bytes')
    return json.loads(raw)


def exit_status(result):
    if not result['coherent']:
        return 2
    status = result['execution']['status']
    return 0 if status in ('returned', 'returned_true') else (
        1 if status in ('reverted', 'returned_false') else 2)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode')
    modes.add_parser('demo', help='offline comparison of two real historical ZTO observations')
    joined = modes.add_parser('compare', help='validate separate Code Lens and Call Rehearsal files')
    joined.add_argument('code_observation')
    joined.add_argument('call_observation')
    replay = modes.add_parser('replay', help='offline validation of a collected context bundle')
    replay.add_argument('bundle')
    live = modes.add_parser('live', help='read-only same-block collection; defaults to ZTO totalSupply')
    live.add_argument('--rpc', choices=call.ENDPOINTS, default=call.ENDPOINTS[0])
    live.add_argument('--token', choices=call.TOKENS, default='ZTO')
    live.add_argument('--to')
    live.add_argument('--sender')
    live.add_argument('--data')
    live.add_argument('--value', default='0', help='native wei, unsigned base units')
    live.add_argument('--returns', choices=('raw', 'uint256', 'bool'))
    live.add_argument('--expect-effective-hash', help='independently reviewed runtime hash')
    live.add_argument('--save', help='new workspace JSON file; existing files refused')
    args = parser.parse_args(argv)
    try:
        if args.mode in (None, 'demo'):
            here = Path(__file__).resolve().parent
            result = compare(read_json(here / 'code-observation.json'),
                             read_json(here / 'call-observation.json'))
        elif args.mode == 'compare':
            result = compare(read_json(args.code_observation), read_json(args.call_observation))
        elif args.mode == 'replay':
            result = verify(read_json(args.bundle))
        else:
            custom = any(value is not None for value in (args.to, args.sender, args.data))
            if custom:
                call.require(all(value is not None for value in (args.to, args.sender, args.data)),
                             'custom calls require --to, --sender and --data together')
                call.require(args.token == 'ZTO', '--token cannot select a custom target')
                tx = {'to': args.to, 'from': args.sender, 'data': args.data,
                      'value': hex(call.amount(args.value))}
                returns = args.returns or 'raw'
            else:
                call.require(args.value == '0', 'token supply demo cannot carry ETH value')
                tx = {'to': call.TOKENS[args.token], 'data': '0x18160ddd', 'value': '0x0'}
                returns = args.returns or 'uint256'
            tx = call.transaction(tx)
            destination = call.workspace_path(args.save) if args.save else None
            if destination:
                call.require(not destination.exists(), 'save path already exists')
            bundle = capture(RPC(args.rpc), tx, returns, args.expect_effective_hash)
            result = verify(bundle)
            if destination:
                encoded = json.dumps(bundle, indent=2) + '\n'
                call.require(len(encoded.encode()) <= LIMIT, 'bundle exceeds 98000 bytes; not saved')
                with destination.open('x', encoding='utf-8') as handle:
                    handle.write(encoded)
        print(json.dumps(result, indent=2))
        return exit_status(result)
    except (ValueError, KeyError, TypeError, AttributeError, OSError, OverflowError, call.RPCError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
