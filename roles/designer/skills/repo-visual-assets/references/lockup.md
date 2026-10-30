# Lockup SVG (mark + name + tagline)

The README-top asset: two SVGs, `logo-lockup.svg` (light) and `logo-lockup-dark.svg`
(dark), switched with one `<picture>` tag inside `<p align="center">`, width ~380.

## Rules

- Every value from the design system, never typed by hand:
  - mark: copy the `<svg>` inner content of `logo.svg` / `logo-dark.svg` unchanged
    (strip its `<title>`), keep its viewBox units (e.g. 128) as the lockup height;
  - colours: `color.<theme>.ink` for the name, `color.<theme>.dim` for the tagline,
    read from `design/tokens.json`;
  - fonts: the token roles (`font.title` for the name, `font.sans` for the tagline),
    files from `design/fonts/`.
- Write letters as OUTLINES (`<path>`), never `<text>`: GitHub serves a README SVG as
  an `<img>`, which cannot load web fonts, so live text falls back to the reader's
  system font.
- Shape with HarfBuzz so kerning is the font's own; set variable axes by tag (`wght`,
  `opsz` = size when present); tracking for the caps tagline ~0.24 em, no trailing
  tracking after the last letter.
- Round path numbers to 2 decimals (file ~12-16 KB, no visible change).
- Italic title fonts overhang left: nudge the tagline ~2 units right so both lines
  look aligned.

## Run (installs nothing in the project venv)

```
uv run --no-project --with fonttools==4.66.1 --with uharfbuzz==0.56.2 \
    python docs/assets/src/lockup.py ["TAGLINE"] [out-dir]
```

The script takes the tagline and an output dir so each option renders into
`_private/art/lockup/<a|b|c>/` with the committed code; the default writes the finals
to `docs/assets/`.

## Core (fontTools + uharfbuzz)

```python
face = hb.Face(hb.Blob.from_file_path(path)); font = hb.Font(face)
font.set_variations(axes)                      # {"wght": 500, "opsz": 82}
buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
hb.shape(font, buf, {"kern": True, "liga": True})
gs = TTFont(path).getGlyphSet(location=axes); order = tt.getGlyphOrder(); k = size / face.upem
for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
    pen = SVGPathPen(gs)
    gs[order[info.codepoint]].draw(TransformPen(pen, (k, 0, 0, -k, x + (pen_x + pos.x_offset) * k, base)))
    pen_x += pos.x_advance + tracking * face.upem
```

## Show before commit

Render every tagline option in GitHub light and dark panes with the README's first
paragraphs under it (headless Chrome screenshot, see SKILL.md section 4), save the PNG
in `_private/art/lockup/`, check it with vision, give the owner the path.
