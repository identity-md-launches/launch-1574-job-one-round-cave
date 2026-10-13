# Pepe 01 — The Step Before the Step

Pepe rehearses a path around a pit before taking the first step.

The faint route approaches a charcoal pit; the stronger ochre tracks turn around it. This represents testing a proposed contract call before committing to execution. Line 4 had no previous painting, so this first mark starts with the supplied bare Moss cave. The majority of the wall remains available for later Pepes.

| Output | Format | Dimensions | Bytes |
| --- | --- | --- | ---: |
| `artifacts/line-4/wall.png` | PNG, RGB | 1254 × 1254 | 2,884,705 |
| `dist/line-4/01.jpg` | Baseline JPEG, three components | 512 × 512 | 51,792 |

PNG SHA-256: `cc122bbdbe73d34b0c096d01ac831203103ac19874f716813c3bfee0e38ecc97`.

## Chosen visual review

Inspected the supplied cave, the full generated wall and the actual saved JPEG through the image viewer. The square dimensions match the original. The framing, cave floor, rock formations, cracks and warm light remain visually aligned with the reference. Pepe has a wide mouth and heavy-lidded eyes. Charcoal and ochre show rock texture through worn pigment. The visible spread hand has five digits: four fingers and one thumb. The other hand is hidden; the three-toed shapes below the body are feet. There are no handprints or hand stencils.

No visible text, digits, captions, signatures, logos, watermarks, borders, frames, real people, political or hateful symbols. The added figure is a flat cave painting, not a photograph or 3D render. **Unmet visual requirements observed: none.** Cave preservation is a visual assessment, not a claim of pixel-identical background preservation. The hand is easier to count on the full wall than on the thumbnail.

Only the final wall and required numbered JPEG were saved as pictures in this workspace. The JPEG's location follows the explicit requirement to place it beside the JSON; this is the specific exception to the general pictures-under-artifacts wording. The PNG remains untracked for separate upload.

## Generation method and final prompt

Used the imagegen skill and built-in image editor with `.imd/reads/artifacts/cave` as the sole edit reference. Imported the actual returned image bytes into the wall path. No CLI image-generation fallback was used. The standard-library `thumbnail.py` helper only resizes and encodes the required JPEG.

Final prompt:

> Edit the supplied bare cave image. Save the finished PNG directly as artifacts/line-4/wall.png in the workspace if supported. Keep the exact square 1254 by 1254 size, the cave rock, all cracks, warm torchlight, colours, floor, and framing unchanged. Add one modest prehistoric cave painting occupying only the middle-left portion of the wall, leaving much bare rock for future painters. Main figure: recognizably Pepe the frog with wide mouth and big heavy-lidded eyes, simple ancient burnt-stick lines and earth pigment smudges, worn ochre and charcoal on rock, NOT a modern cartoon sticker. He crouches looking at two sets of tracks: a faint ochre dotted path approaching a little charcoal pit, and a firmer red ochre path safely bending around it. This symbolizes rehearsing a step before taking it. Show one plainly spread hand with exactly FIVE digits, four fingers and one thumb, easy to count. His other arm ends hidden behind his body: no second visible hand. Feet simple frog feet. Only red/yellow ochre, charcoal black, chalk white and bare stone in the painted additions. Pigment rubbed onto existing uneven rough rock, cracks and texture visible through the marks. No letters, no numbers, no captions, no logos, no signatures, no watermarks, no border or frame, no real people or political symbols. Not photography or 3D for the added painting. Preserve input environment precisely; do not redraw the whole cave.
