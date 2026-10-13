# Local checks — Pepe 01

Completed locally on 2026-10-13. These results are contributor checks, not independent verification.

- **Offline Python suite:** 16 tests passed with `python3 -B -m unittest discover -s line-1/tools/zto-band -p 'test_*.py' -v`.
- **Real-chain arithmetic comparison:** 8 of 8 cases matched the deployed Uniswap v4 quoter exactly at Ethereum block 26183687. Raw calldata and returns are retained in `tools/zto-band/quoter-check.json`.
- **README demonstration:** the documented offline command exited 0 and reported 1 ZTO input, 0.0125 ZTO fee, and 0.000015282142320759 IMD output from the supplied historical observation.
- **PNG:** signature, every chunk CRC, decompressed raster length, RGB format, and 1254 × 1254 dimensions checked. File length: 2,894,032 bytes.
- **JPEG:** valid SOI/EOI markers and frame dimensions checked; 512 × 512, 8-bit, 93,157 bytes. Also decoded and visually inspected with the image viewer.
- **Record:** exactly one numbered JSON (`dist/line-1/01.json`), exact requested top-level/attribute keys, numeric Number 1, and image URL matching the PNG's SHA-256.
- **Wall SHA-256:** `001f38049f5c4a019a0cf38233bbebe9b5aa94f663819d3bd664137e2c931759`.
- **Original cave:** source SHA-256 still `250525790c1987cbb52114bd4e77926f023ac1dc10b73ffc2e1f56e32dfb8a36`.
- **Goal:** the first-created one-line goal remains unchanged.
- **Size and scope:** every delivered file outside `artifacts/` is below 100,000 bytes. Changes are confined to `line-1/`, `dist/line-1/`, and `artifacts/line-1/`. No dependency installation or configuration edits. The required wall output remains untracked.
- **Visual review:** full PNG and JPEG inspected; findings, prompt, and limitations are in `VISUAL.md`. No unmet visual requirement was observed.

Remaining capability limits are deliberate: one price interval only, no transaction preparation/execution, no token-transfer/router simulation, and no cryptographic proof of RPC data. The observation is historical and labeled with its block/time.
