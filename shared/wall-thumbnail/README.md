# Wall thumbnail

Line 4's standard-library PNG reader and baseline JPEG encoder, promoted for reuse with explicit paths. It checks PNG CRCs, accepts opaque 8-bit RGB/RGBA non-interlaced square images of at least 512 pixels, and writes a 512 × 512 JPEG under 100,000 bytes. Source and destination must be inside the current workspace; an existing destination is refused.

From the workspace root, before the requested thumbnail exists:

```sh
python3 -B shared/wall-thumbnail/thumbnail.py artifacts/gathering/wall.png dist/gathering/01.jpg
```

This produced the gathering's actual JPEG: 512 × 512, 52,174 bytes, decoded and visually inspected. It only resamples/encodes the finished wall; it does not paint anything. Repeating the command with the existing output fails intentionally. Choose a new permitted output path for another wall. Python 3.10+; no packages or network.

Original: `line-4/tools/call-rehearsal/thumbnail.py`. The only changes are an argparse input/output interface and exclusive output creation. Its pixel decoder and JPEG encoder are unchanged. Input validation uses assertions, so run ordinary Python without `-O`; this bounded helper is for trusted generated wall assets, not arbitrary hostile image uploads.
