# Checks for Pepe 01

- `python3 -B -m unittest discover -s line-3/tools/code-lens -p 'test_*.py' -v`: 16 tests, all passed offline.
- Code Lens live collection for real ZTO and IMD: succeeded on Ethereum at finalized block 26,183,813. Every code and storage read used its block hash with `requireCanonical: true`. No proxy branch is claimed to have been exercised live; proxy branches use explicitly synthetic tests.
- Offline CLI verification of each saved observation: passed. Reviewed-hash comparison: the actual ZTO hash passed; a different valid-width hash was rejected with exit code 1.
- A separate read-only `eth_getProof` request for each token at that same block: RPC-reported account code hashes matched locally computed runtime Keccak hashes. This was a hash-agreement check, not independent consensus or Merkle-proof verification. Scratch scaffolding is not needed by the delivered tool.
- Structural image inspection: PNG valid, 1254 × 1254, 2,916,521 bytes; JPEG valid, 512 × 512, 60,390 bytes. Full wall and thumbnail visually reviewed; see `VISUAL.md` for the chosen review and its limits.
- Numbered record: exactly the requested top-level and attribute fields; integer number 1; image URL contains the final PNG's lowercase SHA-256; the PNG matches the original cave's dimensions.
- Every new delivered file outside `artifacts/` is below 100,000 bytes. Older tracked files have no changes. Required wall output remains untracked for upload. No packages, configuration files or Foundry changes.

These are local checks, not an independent verifier's certification. Runtime identity is not a safety audit, supported proxy signals are candidates, and report consistency is not proof of chain authenticity.
