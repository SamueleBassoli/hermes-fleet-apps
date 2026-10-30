# Browser-side rules for a no-JavaScript local page

## CSP: the directives that do not inherit

`default-src` is a fallback for **fetch** directives only. Several directives silently
allow everything when unstated — `default-src 'self'` alone does not restrict them:

| Directive | Falls back to `default-src`? | Consequence if omitted |
|---|---|---|
| `script-src`, `img-src`, `style-src`, `connect-src`, `font-src` | yes | covered |
| `form-action` | **no** | a form on the page can post to any origin |
| `base-uri` | **no** | an injected `<base>` re-points every relative URL |
| `frame-ancestors`, `sandbox`, `report-to` | **no** | not covered by a fetch policy |

On a page built out of the user's own filenames, use the full header from the start:

```
Content-Security-Policy: default-src 'self'; form-action 'self'; base-uri 'none'
```

Source: MDN's `form-action` page states "default-src fallback: No. Not setting this allows
anything." Verify against MDN again rather than assuming a directive inherits.

A strict policy also blocks inline `<style>`. Serve CSS as its own route instead of
widening the policy — the same header is what makes an injected script inert, so loosening
it for convenience costs the real protection.

## Answering without JavaScript

- **One tiny `<form>` per button**, the button's own `value` carrying the answer:

  ```html
  <form class="pick" method="post" action="/resolve">
    <input type="hidden" name="index" value="3">
    <button type="submit" name="choice" value="alice">alice</button>
  </form>
  ```

  One form with several buttons needs script to work out which was pressed; this does not.
- **Answer the POST with `303`**, never HTML. A page returned from a POST is re-submitted
  by a refresh, and the second submit acts on something already gone.
- **Escape the value twice over**: once for text, once for the attribute
  (`html.escape(label, quote=True)`), because the label is both the button's text and its
  `value`.
- A control with nowhere to post is rendered `disabled`, not hidden. An inert button that
  says so beats one that silently does nothing — and pair it with a server that returns
  `403` if posted to anyway.
- A completed row should stop requesting media that has been moved or deleted, or the
  browser fires a request the server can only answer with an error.

## Lazy loading, and how to measure it honestly

`loading="lazy"` on an `<img>` costs no JavaScript and no dependency. It matters when each
request is expensive server-side (decode, draw, re-encode) and a real list can hold
hundreds of rows against a single-process server.

**Measuring it with a screenshot reports the wrong answer.** `--screenshot` forces layout
and paint of the whole document, so every image counts as visible and all N are requested.

Recipe that gives a true number:

1. Serve a queue of ~50 items on an ephemeral port.
2. Wrap the handler's `do_GET` to append each media path to a list (a lock and a `set` for
   de-duplication).
3. Launch headless Chrome at the URL with a real `--window-size` and **no**
   `--screenshot`; `Popen`, sleep a few seconds to let first paint settle, then
   `terminate()`.
4. Compare distinct requests against the queue length.

A viewport of 1280x1000 over 50 cards requested 15 — lazy. Same page with `--screenshot`
requested 50 — the instrument, not the page.

## CSS traps that move controls off-screen

**`width`/`height` attributes on `<img>` become presentational hints and beat
`aspect-ratio`.** With no height declared in CSS, the hint wins and every card gets a box
as tall as the source image, pushing the controls below the fold. Keep the attributes —
they tell the browser the ratio before the image arrives and stop the grid jumping — and
declare `height: auto` alongside `aspect-ratio`.

**A `<form>` wrapping each button breaks a button row.** The form is a block-level box, so
a row of choices becomes a column. `display: contents` on the wrapper makes it lay out as
if it were not there.

**A finished card stretched to the grid row height reads as broken** — a large empty
rectangle looks like a failed render. `align-self: start` on the completed variant.

**Any `display:` rule on a class beats the `hidden` attribute.** `hidden` is only a
user-agent `display: none`, so `.grid { display: grid }` keeps a "hidden" panel on
screen, stacked above the view that replaced it. Add `[hidden] { display: none
!important; }` once at the top of the stylesheet, and in a click-through assert the
hidden panel's `offsetParent === null`, not just the attribute.

**Namespace every class in a stylesheet layered over another.** An add-on sheet (a
motion layer loaded after the base CSS) that reuses a short name like `.n` or `.o`
inherits the base sheet's rules for it: a badge's inner digit picked up a round
step-number style and swelled into a circle only mid-animation, which reads as an
animation bug. Prefix add-on classes (`.bo`, `.bn`, `m-*`) and grep the base sheet for
each new name before using it.

**A counter whose digits animate must not change the box size.** Stacking the old and
new number with `position:absolute` + `display:block` changes the line box mid-roll.
Put both in one grid cell (`display:inline-grid` on the badge, `grid-area:1/1` on each
digit, `line-height:1`, `overflow:hidden`) and animate only `transform`.

**Colour by the state that needs action, not by the underlying score.** An item whose
parts all scored "confident" but which still needs a human decision must not be painted
in the confident colour: green reads as "already handled" and is the one card the eye
skips. Decide the tone in exactly one lookup table so the page and any generated imagery
cannot disagree.

**Label generated imagery with digits, not names**, when drawing with OpenCV —
`cv2.putText` renders ASCII only, so an accented name becomes mojibake burned into the
pixels. Names belong in the HTML, which handles Unicode; the digit is the join between
the picture and the list beside it.
