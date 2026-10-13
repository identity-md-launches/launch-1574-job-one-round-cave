# Local check record — Line 2, Pepe 01

Completed on 2026-10-13. These are this contributor's local checks, not independent certification.

- Ran the README's exact offline demo command. Its parsed JSON matched `example-report.json` exactly, with no RPC client or network required.
- Ran `python3 -B -m unittest discover -s line-2/tools/allowance-lens -p 'test_*.py' -v`: **22 tests passed**.
- Captured actual finalized Ethereum state through the supplied provider. The saved audit covers block 26,183,751 and contains 27 Approval events, 19 pairs, 16 owners, and 3 active allowances. All token state calls were pinned to its canonical hash.
- Parsed PNG and JPEG headers: the wall is **1254 × 1254, 8-bit RGB PNG**, matching the source dimensions; the thumbnail is **512 × 512, three-component JPEG**. Both actual files were visually inspected. See [VISUAL.md](VISUAL.md) for digit count, prompt, preservation review, and limitations.
- Wall size: **2,897,281 bytes**. Thumbnail size: **93,460 bytes**. Every new non-artifact file is below 100,000 bytes.
- Wall SHA-256: `dacf1e4a68825c6922473d0e13140dbc1e88c3941e924bee51e6eb3e26604ebd`. The record's image URL contains exactly that hash.
- Checked the new record has exactly `name`, `image`, and `attributes`; its six traits are in the requested shape, and Number is integer 1. Exactly one record exists in `dist/line-2/`.
- All new source/record paths are within line 2's assigned folders. No pre-existing tracked files changed, and no configuration, library, other line, or old record was modified. The required wall is not tracked or staged.
- No package installation, external runtime dependency, wallet, secret, signing, payment, or transaction submission was used. The numbered JPEG follows the explicit requirement to sit beside the JSON record.
