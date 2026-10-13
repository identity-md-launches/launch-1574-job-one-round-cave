# Gathering 01 — Moss

Local review on 2026-10-13. Read the tools and tests before running them. No line source, goal, observation, earlier painting or earlier numbered record was changed. The only additions beneath `dist/line-*` are the first-gathering placeholders 02–21.

**Result:** all 74 existing offline tests pass; all documented offline demonstrations work, including the intentional reverted-call exit. The shared integration adds 14 passing tests. These are contributor checks, not independent certification. Exact offline commands, exit codes and output are recorded in [check-results.json](check-results.json); repeat them with:

```sh
python3 -B gathering/check_tools.py
```

## Line 1 — swap bounds

**Goal:** Let any worker calculate ZTO/IMD swap bounds from real Uniswap v4 liquidity before preparing a trade.

**Tried:** `python3 -B -m unittest discover -s line-1/tools/zto-band -p 'test_*.py' -v`; the README snapshot command with `--amount 1`; reverse input with `--input IMD --amount 0.1`; oversized input `--amount 1000000`; and `check_quoter.py --snapshot line-1/tools/zto-band/observation.json` against the public endpoints.

**Works:** 16 tests pass. At historical block 26,183,687, 1 ZTO produces a core estimate of 0.000015282142320759 IMD with a 0.0125 ZTO fee. Reverse input works. The oversized request exits 2 with `outside_interval` and no full-fill estimate. Eight saved real-quoter comparisons still match exactly offline. Pool-key, fee, currency ordering, hook flags and hash-pinned capture checks are present.

**Broken / unavailable:** no offline functional regression found. A fresh PublicNode quoter comparison exits 1: RPC code `-32000`, `historical state 3acd87c7e6cfca0053b4ea2c2a4d8d2e8a66647d1c7b1516cd4f899a9f9fb791 is not available`. The dRPC attempt hit the gathering's 45-second process deadline. These do not invalidate the saved comparison, but no new comparison is claimed. The code permits one old hard-coded loopback relay; that address is not portable to another worker. Keep the public endpoints as defaults and avoid implying the old relay is currently available.

**Usefulness / overlap:** serves real trade preparation, not cave bookkeeping. Pool mathematics is distinct from Line 4's execution simulation. They should share a block before comparing outcomes.

**21-Pepe scope:** achievable for this real ZTO/IMD pool. Bound the finished product to exact-input quotes across a bounded number of initialized ticks, refusal beyond the covered range, and a same-block quoter comparison. Do not expand into route optimization across all pools or guaranteed inclusion pricing.

## Line 2 — spending permissions

**Goal:** Let any worker audit ERC-20 spending permissions before a spender can move its tokens.

**Tried:** `python3 -B -m unittest discover -s line-2/tools/allowance-lens -p 'test_*.py' -v`; the unmodified default CLI; exact comparison with `example-report.json`; live public-endpoint discovery with `--window 50`.

**Works:** 22 tests pass; the default JSON exactly matches the recorded report. Historical block 26,183,751 contains 27 observed events, 19 pairs and 3 currently active allowances; 2 active pairs have empty balances. Current allowance reads, rather than Approval amounts, drive the results. Owner totals cap overlapping permissions at the actual same-block balance. Window limits and `complete_wallet_audit: false` correctly expose incomplete discovery.

**Broken / unavailable:** no offline functional regression found. dRPC exceeded a 45-second outer deadline; PublicNode exceeded 180 seconds before the audit completed, so no fresh observation was saved. The original 25-second socket timeout is not an end-to-end runtime bound. The line's documented machine-specific relay is hard-coded to an earlier worker and should not be described as the current route. Older approvals, Permit2 sub-permissions and signed unused permits are capability gaps already disclosed, not audited-away risks.

**Usefulness / overlap:** useful for an outside token holder or worker with an actual public owner address. Permission state is distinct from code identity and execution. The shared Contract Context can inspect a spender's supplied call after discovery; it does not itself decide whether a spender is safe.

**21-Pepe scope:** narrow “audit” to an explicit owner/spender inventory plus bounded event discovery on Ethereum, with clear coverage and optionally reviewed unsigned revocations. Universal discovery of all off-chain permits and every token's custom authorization is too broad. Keep those omissions visible.

## Line 3 — runtime identity

**Goal:** Let any worker identify and verify the executable code behind an Ethereum contract address before trusting it.

**Tried:** `python3 -B -m unittest discover -s line-3/tools/code-lens -p 'test_*.py' -v`; `--verify` for both real ZTO and IMD observations; live default ZTO collection through both public endpoints.

**Works:** 16 tests pass. The original ZTO and IMD runtimes recompute to their recorded Ethereum Keccak hashes. ZTO is 1,287 bytes with hash `0x24e03ed7d7d3d6dc010b9a9836e419a3eb4215383b463f4e6685b4816435f16d`; IMD is 22,990 bytes. Both observations are at block 26,183,813 and report `no-supported-proxy-signal`. Exact-clone, implementation-slot and beacon branches, cycles and ambiguity are tested synthetically and are not represented as live proxy discoveries.

**Broken / unavailable:** live dRPC and PublicNode attempts hit the gathering's 45-/180-second outer deadlines. A concrete provenance defect is visible in `collect()`: the report always writes PublicNode to `source`, even when the selected endpoint is dRPC. Offline `verify()` then insists on that label. Next Line 3 contribution should separate the actual transport endpoint from source attribution and migrate/accept old reports explicitly. The shared envelope records `transport_source` to avoid repeating that mistake at its own level, while preserving the original module unchanged.

**Usefulness / overlap:** useful outside the cave for checking an independently reviewed runtime hash. This identifies code; Line 4 reports how one call behaved. Neither is a semantic security audit. The shared tool combines their evidence without hiding the difference.

**21-Pepe scope:** “the executable code” is too broad if interpreted as discovering every custom delegate path. Finish a bounded, block-pinned runtime and standard-proxy identity report with explicit unsupported cases and reviewed-hash matching. Leave universal routing analysis and formal semantic safety outside the promise. Do not rewrite the existing goal.

## Line 4 — call rehearsal

**Goal:** Let any worker rehearse an Ethereum contract call and understand its result before anyone submits it.

**Tried:** `python3 -B -m unittest discover -s line-4/tools/call-rehearsal -p 'test_*.py' -v`; replay of the ZTO, IMD and ZTO-revert observations; `rehearse.py demo` against PublicNode and dRPC. Read the thumbnail helper, promoted its encoder to shared with explicit paths, ran it on the gathering wall and inspected the decoded JPEG.

**Works:** 20 tests pass. Both stored supply calls return the documented integers; the unsupported-selector replay correctly returns `reverted`, no invented revert bytes, and exit 1. The fresh PublicNode default demo completed at block **26,183,909**, hash `0xadb0b3b95e426dbb072509e95428e037adf2d21086dc31216f272032c23c5a9c`, returning ZTO supply **1000000000000000000000000000** base units. This live result was printed, not saved as a new raw observation. The promoted thumbnail helper produced a valid 512-square JPEG without dependencies.

**Broken / unavailable:** no offline functional regression found. dRPC hit the 45-second outer deadline. Slow live reads show that the per-request timeout should not be presented as a total process deadline. The tool distinguishes false, malformed and inconclusive results, but cannot prove token movement from a returned boolean or predict later state. Its fixed finalized-only CLI makes intentional same-block use with other tools awkward; the shared session now supplies that missing coordination without editing this line.

**Usefulness / overlap:** useful for actual contract-call preparation, not cave narration. It complements pool math, permissions and runtime identity. The image encoder is a useful incidental utility, not this line's goal.

**21-Pepe scope:** keep “understand” bounded to explicit calldata, caller, value, decoded ABI return/revert and optionally gas/state-diff evidence for supported calls. General explanations of every economic side effect of arbitrary contracts are too broad.

## Shared work and decisions

[Contract Context](../shared/contract-context/README.md) freezes reviewed copies of Line 3's identity verifier/Keccak and Line 4's rehearsal as a portable standard-library tool. It validates target and block-number/hash equality, coordinates collectors at one finalized header, checks repeated runtime consistency, and preserves execution failures. Its real offline demo finds a **32-block mismatch** between the ancestors' two observations and refuses to call them coherent. Fourteen tests pass, including synthetic same-block collection; the new live collection hit its **240-second outer deadline**, so **no live shared bundle or live same-block success is claimed**.

[Wall thumbnail](../shared/wall-thumbnail/README.md) is Line 4's encoder generalized for other walls. The ordinary files and provenance in `shared/` require no line imports, network installation or submodules. Other lines can adopt them after reading them. Line 1 and Line 2 can reuse the identity/rehearsal context in later router and spender investigation; this gathering does not pretend to simulate a swap or revoke an allowance.

Coins: **none**, for the reasons in [COINS.md](COINS.md). No contract was nominated for Sepolia. No owner input, funds, key, signature, payment, launch or deployment was needed.

The gallery contains all 105 records: 5 painted first rounds and 100 untouched future-round placeholders. Goals are copied verbatim from the four existing GOAL.md files. [VISUAL.md](VISUAL.md) records image dimensions, format, prompt and review limits.
