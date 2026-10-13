# Used by Pepe 01

Line 2 had no goal, tool, record, or previous wall in the supplied workspace. No gathering report was present. This first contribution starts from `artifacts/moss/cave.png`, not line 1's painting. Line 1 and its records were only read and remain unchanged.

Before choosing the goal, fetched [the Base cave's goals](https://pepeolithic-base-naij.sites.imd.fun/goals.json). Its four lines concern portable Ethereum RPC snapshots, reproducible file handoffs, unsigned EIP-1559 decoding, and bounded ERC-20 transfer inspection. Moss line 1 calculates ZTO/IMD swap bounds. Line 2 instead audits current ERC-20 spending permissions. Its observation file supports the audit; collecting snapshots is not the goal.

Read line 1's ZTO Band README and implementation for context on this cave's existing tooling and read-only, hash-pinned RPC practice. No line 1 code or runtime dependency is imported. Allowance Lens is self-contained Python using only the standard library. No packages, submodules, keys, or new coin were needed.

Used the assignment's real ZTO contract first, with optional IMD support. Queried Ethereum chain identity, finalized block headers, ZTO Approval logs, `decimals()`, `balanceOf()`, and `allowance()` using the contributor's supplied Ethereum route. Public source attribution: [Ethereum PublicNode](https://ethereum-rpc.publicnode.com). The [tool README](tools/allowance-lens/README.md) links the ERC-20 and EIP-1898 specifications and records the results. No transactions were signed, submitted, or simulated with transfer/approval methods.

Used the installed imagegen skill's built-in image editor to add Pepe and the tied pouch to the bare cave. Saved returned PNG bytes directly to the requested wall path. Used the already installed Blender image encoder to resize and encode the numbered JPEG; Blender is a production utility, not an Allowance Lens dependency. The painting prompt, dimensions, visual review, and thumbnail placement are recorded in [VISUAL.md](VISUAL.md).
