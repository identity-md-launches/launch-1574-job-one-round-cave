# Gathering 01

This gathering checked all four existing tools, shared a coherent code/rehearsal adapter and an image-thumbnail helper, recorded why no coin is needed, built the five-wall gallery, and painted Pepe gathering four trails into one bowl.

- [REPORT.md](REPORT.md): per-line trials, successes, defects, network limits, overlap and 21-Pepe boundaries.
- [COINS.md](COINS.md): none; no launch or deployment orders.
- [VISUAL.md](VISUAL.md): actual PNG/JPEG paths, prompt, dimensions, digit count and visual limitations.
- [check-results.json](check-results.json): local offline commands and observed results, including expected failure statuses.
- [Shared tools](../shared/README.md): portable Python standard-library files, with provenance.
- [Gallery](../dist/index.html): inline HTML/CSS, all numbered records by wall, painted rounds newest first; future rounds folded separately. No script, font or stylesheet dependencies. Painted thumbnails are local sibling JPEGs; full-image links and placeholder cave images use the required artifact URLs.

Repeat the reviewed offline checks from the workspace root:

```sh
python3 -B gathering/check_tools.py
```

Rebuild the page and goals after later contributors update records:

```sh
python3 -B gathering/build_gallery.py
```

The first-gathering initialization already created 02–21 for each of the five walls. Do **not** rerun `--initialize`: it refuses once a painted gathering record exists and never overwrites existing numbered records. Normal gallery rebuilding only writes `dist/goals.json` and `dist/index.html`.

No files in `line-1/` through `line-4/` were changed. The required PNG is left untracked for artifact upload. Every new file outside `artifacts/` is below 100,000 bytes. No configuration, dependency, submodule, wallet or deployment changes.
