# ZTO Band

Estimate how much ZTO can enter its real Ethereum Uniswap v4 pool before the next possible liquidity boundary, and the corresponding IMD output. The reverse direction is supported too. This is a small, deliberately bounded building block for workers planning a trade: it verifies the assigned pool and uses integer arithmetic to estimate one interval. It does not construct or execute transactions.

## One command to see it work

From the repository root, with Python 3.10 or later:

```sh
python3 -B line-1/tools/zto-band/zto_band.py --snapshot line-1/tools/zto-band/observation.json --amount 1
```

No installation, network, environment variables, keys, or external files are needed. The command replays a **real historical observation**, not a made-up pool. It prints JSON estimating **1 ZTO → 0.000015282142320759 IMD**, including a **0.0125 ZTO** pool fee, at Ethereum block **26183687**, timestamp **2026-10-13 12:51:35 UTC**. This is the observation time, not a live price.

Omit `--amount` to calculate the supported interval's input cap. For the recorded state this is **935043.391050033044714331 ZTO**, with estimated output **14.252367975752031679 IMD**. The estimated movement of the token1/token0 spot ratio is **52.126811053758943732445132 basis points**. This cap describes this tool's narrow interval, not all liquidity in the pool or a recommended trade size.

Use `--input IMD --amount 0.1` for the reverse direction. Amounts must be plain decimal strings with no more precision than the token supports. Raw token amounts are strings in the output to avoid JSON/JavaScript precision loss.

## Fresh observation (optional network)

```sh
python3 -B line-1/tools/zto-band/zto_band.py --live --amount 1 --save line-1/tools/zto-band/fresh-observation.json
```

The default RPC is [Ethereum PublicNode](https://ethereum-rpc.publicnode.com). An explicit `--rpc https://eth.drpc.org` is also possible. A provider must support archival reads and EIP-1898 block-hash `eth_call`. The default block tag is `finalized`; `--block safe`, `--block latest`, or a decimal block number is accepted. Every state call uses the same block hash with `requireCanonical: true`, and the header is checked again after capture. A reorg or unavailable block produces an error rather than mixed state. Requests carry `Pepeolithic-ZtoBand/1.0` as User-Agent. Each call has a 30-second timeout, a response-size bound, and no automatic retry loop.

All on-chain operations are reads: chain identity, block headers, one Initialize log, and `eth_call`. The tool has a method allowlist, disables environment-derived HTTP proxies, rejects credential-bearing RPC URLs and redirects, and restricts user-selected file paths to the current workspace. Source data is from the assignment's Ethereum provider, identified here by the task's public RPC source. No wallet, balance, approval, signature, or transaction is needed.

## What is verified

- Ethereum chain ID 1 and the StateView's PoolManager address.
- The Initialize event in block **26129224**, including token order, fee **12500**, spacing **60**, and the Keccak-256 PoolKey hash matching the supplied pool ID.
- IMD is currency0 (`0xd34a99bc0f67ae1bbd63c660e6d0b0dd03e263b7`); ZTO is currency1 (`0xd782bdea4ef02a0bd391eb9089470c8080f0a68e`). Both recorded token decimals are 18, read on-chain rather than assumed.
- Canonical ABI widths, signed tick encoding, price/tick consistency, initialized price, fee bounds, and liquidity width.
- The real hook `0x784ff9a3ac5d88a30bfff6f7f2a270161fbe6000` has no swap callback/delta permission bits. Swap hooks are refused if encountered; dynamic fees are unsupported.

## Calculation and boundaries

The nearest multiple-of-60 ticks enclose a range with no possible initialized liquidity tick in its interior. The tool uses current active liquidity and stops one Q96 unit inside the relevant boundary. Input rounds up, output rounds down, and fees follow v4's directional protocol-plus-LP fee calculation. ZTO input increases `sqrtPriceX96`; IMD input decreases it. Tick-to-price conversion follows Uniswap's integer TickMath constants, including negative ticks. The pool's spot IMD/ZTO ratio is the reciprocal of the raw token1/token0 ratio, adjusted for decimals.

For a requested amount inside the supported range, `estimate` gives the output, fee, ending square-root price, and consumed/unspent input. Omitting the amount estimates the interval cap with its explicit price limit. A request above that cap returns `outside_interval` and **no estimate**; no partial result is presented as a full fill. Zero liquidity or an exact boundary with no room in the chosen direction returns `no_interval_capacity`.

Exit codes: **0** estimate produced; **2** valid observation but insufficient interval capacity; **1** invalid input, unsupported state, or failed RPC. Errors are JSON on stderr; successful/unsupported-capacity reports are JSON on stdout.

This is core pool math, **not an executable quote or minimum-received guarantee**. It does not traverse initialized ticks, assess token transfer behavior, execute router settlement, price gas, choose slippage tolerance, simulate MEV, or prove RPC responses cryptographically. The saved data is historical. Very tiny inputs can be entirely consumed by rounding/fees and yield zero output. Future pieces can add initialized-tick traversal and execution simulation without replacing this bounded primitive.

## Checks and what happened

```sh
python3 -B -m unittest discover -s line-1/tools/zto-band -p 'test_*.py' -v
```

**16 tests passed.** They cover Keccak vectors, TickMath extrema, negative tick division, directional fees, exact rational delta rounding, pool identity, malformed observations, input precision, boundary states in both directions, zero liquidity, cap refusal, monotonic output, amount conservation, RPC method restrictions, reorg detection, and offline operation with RPC construction forbidden.

The deployed [V4Quoter](https://etherscan.io/address/0x52f0e24d1c21c8a0cb1e5a5dd6198556bd9e1203) independently returned identical raw outputs for **eight cases** at the same recorded block: ZTO inputs of 1 raw unit, 1, 1000 and 400000 tokens; IMD inputs of 1 raw unit, 0.001, 0.1 and 1 token. `quoter-check.json` retains the calldata and raw return bytes. Offline tests replay those comparisons. They are local evidence, not an independent certification.

To repeat the comparison through read-only `eth_call` (requires network and archive state):

```sh
python3 -B line-1/tools/zto-band/check_quoter.py --snapshot line-1/tools/zto-band/observation.json
```

The node simulates the quoter and discards all changes. Nothing is signed or broadcast. The checker accepts `--rpc` and `--save` for an explicit endpoint and a workspace JSON evidence file. If a case exceeds the observation's interval it is marked skipped; the supplied observation fits all eight cases.

## Files and sources

`zto_band.py` is the CLI and validator; `math_core.py` is the integer calculator; `keccak.py` is a small standard-library Ethereum hash implementation. `observation.json` is the real pinned state, `quoter-check.json` is the independent on-chain-call comparison, and `test_zto_band.py` is the offline suite. No third-party runtime dependency or downloaded executable is needed.

- [Official Uniswap v4 Ethereum deployments](https://developers.uniswap.org/docs/protocols/v4/deployments)
- [StateView source](https://github.com/Uniswap/v4-periphery/blob/main/src/lens/StateView.sol)
- [TickMath](https://github.com/Uniswap/v4-core/blob/main/src/libraries/TickMath.sol), [SqrtPriceMath](https://github.com/Uniswap/v4-core/blob/main/src/libraries/SqrtPriceMath.sol), [SwapMath](https://github.com/Uniswap/v4-core/blob/main/src/libraries/SwapMath.sol), [ProtocolFeeLibrary](https://github.com/Uniswap/v4-core/blob/main/src/libraries/ProtocolFeeLibrary.sol)
- [Initialize transaction](https://etherscan.io/tx/0x39c8e5c567e295c1eace7243a2d6eca7a64f1bfcc05a4d51b5f3192671427630)
- [Observed block](https://etherscan.io/block/26183687)

The adapted Uniswap arithmetic is MIT-licensed; its notice is included in `LICENSE-Uniswap.txt`.
