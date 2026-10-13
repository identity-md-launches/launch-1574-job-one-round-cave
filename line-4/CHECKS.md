# Checks for Pepe 01

- `python3 -B -m unittest discover -s line-4/tools/call-rehearsal -p 'test_*.py' -v`: **20 tests passed**, offline. The large-runtime regression test was added after IMD exposed an overly small initial data limit.
- Live ZTO and IMD `totalSupply()` calls succeeded at finalized Ethereum blocks 26,183,845 and 26,183,877 respectively. Both state reads in each rehearsal used the same canonical block hash. Observations are included as ordinary small JSON files.
- A live unsupported-selector ZTO probe reverted with RPC code 3 and no revert bytes. Its replay exits 1 as expected. Sender was the real, assignment-supplied IMD contract address, used solely as an explicitly labeled negative-probe caller. No key or transaction was involved.
- Offline CLI replay of saved ZTO and IMD observations exits 0. Offline replay of the saved revert exits 1. No network is needed to run the documented first command or the tests.
- PNG signature, IHDR dimensions, and all PNG chunk CRCs checked by the standard-library thumbnail helper. Actual JPEG decoded in the image viewer; both full wall and thumbnail visually inspected. Dimensions: PNG 1254 × 1254; JPEG 512 × 512. See VISUAL.md for visual review and limits.
- Record 01 has exactly the requested four top-level keys and six attributes; Number is integer 1; the image URL uses the final PNG's lowercase SHA-256.
- All delivered files outside artifacts are below 100,000 bytes. Only line-4, dist/line-4 and the required artifacts/line-4 output were added. Older tracked work has no changes. No configuration changes, installations, submodules or external runtime dependencies. Required wall is left untracked for the upload daemon.

These are local checks, not independent certification. Simulation results and saved observations remain provider-reported, and a successful historical rehearsal does not guarantee future execution or intended economic effects.
