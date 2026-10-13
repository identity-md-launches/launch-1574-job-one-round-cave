# Pepe 01 — The Measured Pool

Pepe measures the pool between two stones before taking a step.

The mark connects to ZTO Band's first working piece: measuring the liquidity available in a bounded interval before considering a trade. This is the first painting on the supplied bare cave, so there were no ancestor marks to overwrite or remove. The goal in `GOAL.md` was created once and retained.

## Delivered images

| File | Format | Dimensions | Purpose |
| --- | --- | --- | --- |
| `artifacts/line-1/wall.png` | PNG, RGB | 1254 × 1254 | Full square wall, matching the input size |
| `dist/line-1/01.jpg` | JPEG, RGB | 512 × 512 | Required numbered thumbnail beside `01.json` |

Only the wall and its requested thumbnail were written as new picture files in the workspace. The thumbnail is beside the record as specifically required by the FILES section. The wall is left untracked for the artifact uploader.

## Visual review

Inspected the full-size generated PNG and the saved JPEG. The original cave's rock contours, cracks, lighting, color, and framing remain visually recognizable and aligned. The new ochre-and-charcoal Pepe has heavy eyelids and a broad mouth, with worn pigment allowing the stone grain to show through. He studies a shallow pool between stones. Both hands were counted as **five digits each: four fingers and a thumb**. No additional hands or handprints were added. No letters, numbers, logos, borders, signatures, watermarks, real people, or political/hateful symbols were observed.

Unmet visual requirements observed: **none**. This is a visual inspection, not a claim of pixel-identical rock preservation; the image was generated as an edit. JPEG compression softens small finger details at thumbnail scale; the full PNG is the primary wall.

## Method and final generation prompt

Built-in `image_gen` image-edit mode, with the supplied cave as the sole edit target. No CLI/API-key fallback. Generated PNG bytes were written directly to the declared wall path. Blender resized and JPEG-encoded the thumbnail without rendering a new scene.

> Use case: precise-object-edit. Edit target: the supplied bare cave wall, square 1254 x 1254. Preserve the exact cave, every rock edge and crack, warm torchlight colors, framing and dimensions. Add only one modest prehistoric pigment painting occupying the upper-middle left part of the broad lit central stone, leaving most of the cave untouched for future marks. The painting is Pepe the frog as an ancient cave figure with unmistakably broad frog head, two big heavy-lidded eyes, a wide expressive downturned mouth, squat body in a charcoal contour with rubbed yellow ochre and red ochre pigment. Handmade like Lascaux, rough worn pigment catches on the original stone grain, bare rock shows through. He crouches beside a little shallow ochre pool contained between two charcoal stones, studying the water's level: a symbol of measuring available liquidity before a swap. Show his two small hands clearly resting on his knees; EACH hand has exactly FIVE digits: four fingers plus one thumb, never four or six. No extra hands or handprints. Earth pigments only charcoal black, red ochre, yellow ochre, chalk white. Keep drawing simple and flat, not 3D or a photograph of a frog. No letters, no numbers, no text, no arrows, no captions, signatures, logos, watermarks, frames, borders, political symbols. Keep the original cave surface and framing unchanged outside the small new painting. Output a square PNG retaining input size.
