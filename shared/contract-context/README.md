# Contract Context

Check whether a code-identity report and a contract-call rehearsal describe the same Ethereum target at the same block. This prevents a worker from treating separately collected, internally valid observations as one coherent preflight check.

Python 3.10+ and the standard library only. The entire folder is portable; run from the root of the workspace containing it. No keys, environment inspection, signing, broadcasting, external files or dependency installation.

## One command

```sh
python3 -B shared/contract-context/context.py demo
```

This compares two unchanged **real historical ZTO observations**. It returns `context_mismatch`, `same_target: true`, `same_block: false`, and **exit 2 as intended**: Code Lens observed block 26,183,813 while Call Rehearsal observed 26,183,845. The 32-block gap is not silently removed. The output retains the runtime hash and decoded supply but explicitly refuses a same-block claim. This is a working negative demonstration, not fabricated matching evidence.

```sh
python3 -B -m unittest discover -s shared/contract-context -p 'test_*.py' -v
```

Fourteen offline tests passed. They check the real mismatch and explicitly synthetic transport branches: one finalized-block selection, hash-pinned reads, changed headers, conflicting code, target/hash/number mismatch, tampering, revert/false/unknown returns, workspace bounds and read-only method guards. Synthetic responses exist only in tests, never as claimed chain observations.

## Combine your own observations

`compare CODE_OBSERVATION CALL_OBSERVATION` accepts the original tools' JSON formats. `replay BUNDLE` validates a bundle created by this tool. Paths must resolve inside the current workspace; input and saved bundles are limited to 98,000 bytes. Validation errors use stderr and exit 2.

For a fresh read-only capture:

```sh
python3 -B shared/contract-context/context.py live --save shared/contract-context/fresh-context.json
```

The default is real ZTO `totalSupply()`; `--token IMD` selects IMD. `--rpc https://eth.drpc.org` selects the other task-provided public source. A provider must support finalized headers and EIP-1898 hash-pinned reads. Save uses exclusive creation: choose a new workspace filename each time. A large proxy path may exceed the file bound and is refused rather than truncated.

Custom calls require **all** of `--to`, `--sender`, and `--data`, using actual addresses and exact calldata supplied by the caller. `--value` is unsigned native wei (default zero); `--returns raw|uint256|bool` defaults to raw for custom calls. No sender is invented. `--expect-effective-hash` accepts an independently reviewed Ethereum runtime hash. Simulation with a public sender does not prove control of that sender.

The shared session chooses one finalized block, makes both collectors read that block, checks every state read's hash, rechecks headers, and compares repeated target runtime reads. It preserves Code Lens's proxy candidates and Call Rehearsal's actual outcome. Revert or false remains exit 1 even when the context matches; an unknown return or mismatched context is exit 2; coherent returned/true is exit 0. Matching evidence is **not** an endorsement, economic proof, future execution guarantee, gas estimate or receipt.

The network client sends `Pepeolithic-CallRehearsal/1.0`, disables automatic proxies/redirects and allows only chain/header/code/storage reads and `eth_call`. HTTP POST here carries read-only JSON-RPC calls; it never posts a transaction or a launch request. Per-request socket timeouts do not guarantee a total process deadline, especially during DNS lookup. The gathering bounded its live attempts with an outer process timeout.

## Provenance

- `code_lens.py` and `keccak.py` are byte-for-byte copies of Line 3's initial Code Lens. The hash primitive can also serve Line 1's selectors and future Line 2 calldata work.
- `rehearse.py` is a byte-for-byte copy of Line 4's initial Call Rehearsal.
- `code-observation.json` and `call-observation.json` are unchanged copies of those lines' real ZTO observations.
- `context.py` and `test_context.py` are this gathering's glue and tests.

The copies deliberately freeze the tested interface and keep this folder usable without the cave's line layout. The source hashes are listed in `provenance.json`; future updates should recopy reviewed versions and rerun the integration tests. No original file is changed.

Code Lens's nested `source` field is fixed to PublicNode by its original implementation. A collected context's `transport_source` preserves the actual selected endpoint; the nested source must not be read as proof of transport provenance. All offline checks establish internal consistency only, not consensus or RPC honesty. Supported proxy slots remain candidate routing signals rather than proof of which code executed.
