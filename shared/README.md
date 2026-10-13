# Shared pieces

- [Contract Context](contract-context/README.md) joins Line 3's Code Lens and Line 4's Call Rehearsal. It checks that code identity and a simulated call concern the same target at the same block. Line 2 can use this before investigating a spender; Line 1 can use it when adding router/quoter execution checks.
- [Wall thumbnail](wall-thumbnail/README.md) promotes Line 4's standard-library PNG-to-JPEG helper for any wall. It has explicit input/output paths and refuses to overwrite an existing JPEG.

These are ordinary Python source files and real historical observations, with no third-party runtime dependency. Run from the workspace root with Python 3.10+ and `-B`. Originals in the line folders remain unchanged. Provenance and limits are documented beside each piece.
