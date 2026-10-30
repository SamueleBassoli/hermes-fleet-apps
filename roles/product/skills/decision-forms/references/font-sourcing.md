# Sourcing shippable fonts for a comparison sheet

Goal: every candidate font is a local file with its licence beside it, so the
sheet renders offline and the chosen set can ship inside the app unchanged.

## Where to fetch (primary sources, curl, no install)

- Google Fonts families: raw files from the `google/fonts` repo,
  `https://raw.githubusercontent.com/google/fonts/main/ofl/<family>/<File>.ttf`
  (variable fonts are named `Family%5Baxes%5D.ttf`, URL-encoded brackets; italics
  are a separate `Family-Italic%5Bwght%5D.ttf`) and `.../ofl/<family>/OFL.txt`.
  The `ofl/` folder itself is the licence claim; still save OFL.txt beside the font
  (name it `OFL-<family>.txt` so several share one folder).
- A project on GitHub with no fonts in the tree: check its releases
  (`api.github.com/repos/<o>/<r>/releases/latest` -> `browser_download_url`).
  Microsoft's Selawik (free Segoe UI stand-in) ships this way, OFL.
- TeX-world fonts: CTAN mirror, `https://mirrors.ctan.org/fonts/<name>/...`.
  Domitian (free Palatino stand-in, from URW's Palladio) lives there.
- Check every download with `-w "%{http_code} %{size_download}"`: a 404 page
  is saved as a 14-byte "font" otherwise. Batch the downloads in one
  execute_code loop over a {filename: url} dict.

## Licence check

Read the licence file itself, not a catalogue page. One-line sweep over the
folder: `for f in OFL-*.txt; do grep -q "SIL OPEN FONT LICENSE Version 1.1" $f || echo BAD $f; done`.
Some fonts are multi-licensed (Domitian: AGPL-with-exception, OFL, LPPL, "at your
option"): name which licence the project takes (OFL) on the sheet.

## Candidate pools that worked

| Role | Options (all OFL, on google/fonts unless noted) |
|------|-----------------------------------------------|
| App sans, current | Geist, Inter, Space Grotesk, Manrope, Plus Jakarta Sans |
| Numbers (mono) | Geist Mono, JetBrains Mono, Space Mono, Fira Code, DM Mono |
| Art title, italic | EB Garamond Italic (Venetian/Aldine), Cormorant Garamond Italic, Playfair Display Italic |
| Art title, script | Pinyon Script (copperplate), Great Vibes (flowing) |
| Classical caps | Marcellus, Cinzel (caps only), Domitian (CTAN) |

## Free look-alikes for common system fonts

| System font (cannot ship) | Free stand-in (OFL)              |
|---------------------------|----------------------------------|
| Palatino / Palatino Linotype | Domitian                      |
| Segoe UI (Light)          | Selawik (Light)                  |
| Consolas                  | Inconsolata                      |
| Trajan (carved capitals)  | Marcellus, Cinzel (caps only)    |

## Sheet layout

For a page served by Lavish, `@font-face` must carry the font INLINE as base64
(linked files are dropped by its sandboxed iframe, see SKILL.md). Build the page
from Python so the embedding is a function, not hand-pasted data:

```python
def face(fam, file, w="400", style="normal"):
    mime = "font/otf" if file.endswith(".otf") else "font/ttf"
    b = base64.b64encode((U / "fonts" / file).read_bytes()).decode()
    return (f'@font-face {{ font-family: "{fam}"; src: url("data:{mime};base64,{b}"); '
            f'font-weight: {w}; font-style: {style}; }}')
```

Give variable fonts a weight range (`"100 900"`). A 10-16 font sheet weighs 3-6 MB;
fine locally. One CSS rule per role (art title / app text / numbers) per option,
so a "mix" answer maps straight to the roles. Keep the loose font files and
licences in the prototype's gitignored folder until the pick; only the chosen set
moves into the package.
