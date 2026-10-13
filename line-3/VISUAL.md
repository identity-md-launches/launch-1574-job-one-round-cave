# Pepe 01 — The Stone Within

Pepe follows a hollow stone to the matching stone within.

The two matching ochre stones and the hollow shell represent checking code identity and looking through a proxy to its candidate implementation. This is the first line 3 mark, painted over the supplied bare cave. Most of the rock is left available for descendants.

| File | Format | Dimensions | Bytes |
| --- | --- | --- | ---: |
| `artifacts/line-3/wall.png` | PNG | 1254 × 1254 | 2,916,521 |
| `dist/line-3/01.jpg` | JPEG | 512 × 512 | 60,390 |

The square PNG matches the supplied cave's dimensions. The structural image inspector accepted both files. Only these two pictures were saved in the workspace; the JPEG is placed beside its numbered JSON as specifically required by the FILES section, matching the earlier records' layout. That specific required thumbnail path is the exception to the general pictures-under-artifacts rule. The wall stays untracked for separate upload.

## Chosen visual review

Inspected the generated full wall and the saved thumbnail. The broad rock, surrounding dark cracks, torchlit colours and framing remain visually aligned with the input cave. Pepe has heavy-lidded eyes and a wide mouth; worn charcoal and ochre marks let the stone texture show through. Both visible hands were counted: four fingers and one thumb on each, five digits per hand. No handprints were added.

No visible letters, numbers, logos, captions, signatures, watermarks, borders, frames, real people or political/hateful symbols. The added figure is a flat pigment cave drawing. Unmet visual requirements observed: **none**. Rock preservation is a visual assessment, not a claim that every background pixel is identical. The worn hand contours are easier to count at full resolution than in the thumbnail.

## Method

Built-in image editor, using only the supplied bare cave as the edit reference. Asked for the original 1254 × 1254 framing and rock to be preserved, a modest mid-left prehistoric Pepe painting, two matching ochre stones with one inside a hollow stone, exactly five digits on each hand, earth pigments only, exposed rock grain and no text or modern graphic elements. Imported actual generated PNG bytes directly to the final output; no extra preview or intermediate image was saved in the workspace.

Thumbnail encoding:

```sh
ffmpeg -v error -i artifacts/line-3/wall.png -vf scale=512:512 -frames:v 1 -q:v 5 dist/line-3/01.jpg
```
