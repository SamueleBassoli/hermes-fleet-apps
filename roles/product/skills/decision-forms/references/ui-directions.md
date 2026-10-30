# Building UI prototyping rounds (directions, flow map, full mockup, motion)

## Directions round (redesign step 1)

Goal: 3-4 app styles the owner can tell apart in one scroll, on the SAME two screens
(the core-loop screen + one list screen), each flippable light/dark, all buildable
with what the app already does.

## Before drawing

- Read the real UI's markup and the JS that fills it (e.g. `index.html`, the
  render functions) and the bridge's allowed commands. Every control in a
  mockup must exist in the app or be window-only (keyboard shortcuts); anything
  needing a new CLI capability is flagged, not drawn silently.
- Copy the real labels and states (prompt wording, button order, undo line,
  item + position, status labels), not invented ones.

## Directions that read as different (worked set)

Name each after apps the owner knows, one line on what it trades away:

| Id | Style | Reference | Trade-off |
|----|-------|-----------|-----------|
| A | Calm: soft sidebar, air, stacked big buttons | a system settings app | least "techy" |
| B | Precise: top tabs, dense, table list, key hints on buttons | a developer tool | most "tool" |
| C | Content first: frameless, controls over the content, pill dock, round thumbnails | a media app | least text |
| D | Tied to the art: caption-style headings in the art's title font, hairline rules, square buttons | the project's own art | most distinctive |

Give a recommendation that may be a mix (e.g. B's speed + D's headings).

## Build recipe

- Generate the page from Python: one function per (direction, screen) returning
  HTML, one CSS class per direction holding its own custom-property set
  (`--bg --ink --dim --line --blue --amber ...`) and `body.dark .X {...}`
  flipping them. One sticky Light/Dark toggle flips all directions at once.
- Each screen is a fixed-height `.win` (e.g. 640 px) so directions compare at
  the same window size; check nothing important falls below its fold.
- Pick form at the bottom: one radio per direction + "Mix" + a note box.

## Sample content

- Public sample media only (public-domain or CC0, licence noted). If the app
  detects or labels things in the media, run the project's own code on the
  sample to get the boxes and labels, so the mockup lines up with real output.
- Made-up names must fit what they label (one name per item, plausible for it):
  a mismatch reads as a bug in the product, not the mockup.

## Verify every state the owner will see

- Screenshot through the Lavish session URL, then zoom on EACH direction: look
  for a primary button that lost its colour (a later, more specific rule like
  `.X .btn { background: ... }` overrides `.btn.pri`: restate `.X .btn.pri`).
- The non-default state (dark) cannot be clicked from outside: Lavish's
  sandboxed iframe is out of reach of the top page's CDP session. Give the
  build script a `--dark` flag that writes `<body class="dark">`: build with
  it, screenshot, rebuild without it, and `grep -c '<body>'` the file (1) before
  handing over. Rebuilding beats hand-editing the file, which can be left dark.
  Lavish serves the file live, so the same session URL shows each rebuild.
- Take ONE tall capture per state (`CDP_SIZE=1400,<page height>`), then zoom
  with vision `region` on each screen. Check every side column's right edge.
  A grid track written `1fr` grows to its content's minimum width (a wide
  image), which pushes the fixed column past the window and clips its text.
  Use `minmax(0,1fr)` and `min-width:0` on grid/flex children that hold media.

## Flow-map round (redesign step 2)

Goal: the owner decides WHAT sits where and HOW to move, not the look. One page:

1. **A flow diagram first** (inline SVG): one box per screen, where the app
   opens (first launch vs later launches), the buttons that jump between
   screens (solid arrow) and links (dashed), the main loop drawn fat.
2. **Every screen as a grey wireframe** in the picked direction's layout, same
   fixed-height `.win`, images `filter:grayscale(1)`, one dark-grey primary
   button, no accent colour (colour is the next step, so it cannot distract).
   Show the screen in its most informative state (preview done, a detail
   panel open, an item with its undo line), with the real labels.
3. **Each control carries a dashed grey tag with the CLI command it runs**
   (`run --apply --progress`). It proves the "UI mirrors the CLI" rule on the
   page itself and shows which button does what; say the tags are not
   part of the app.
4. **Picks = structure only**: tab order (2-3 orders, each drawn as a mini
   header strip, the recommended first with its reason) plus any one layout
   question the current app answers badly (e.g. a folder asked on two screens
   vs once in the header), plus a note box.

Before drawing, map the app's current navigation from the JS (the `show()`
calls: which screen opens at launch, which button jumps where), since that is
the baseline the options vary.

**Do not draw data the CLI does not return.** Check each column and label
against the command's `--json` fields (e.g. a column for a field the listing
does not return). Drop it, and put a one-line note on the page
that it would need a CLI field first; same for any option that needs persisted
state the CLI lacks (remembering a folder between launches). Label such
options on the page, never recommend them silently.

## Full-mockup round (redesign step 3)

Goal: the picked style on EVERY screen, in the picked flow, light and dark,
so the owner judges the finished look once. Build a new script and CSS
(`build_mockup.py` + `mockup.css`) beside the earlier rounds' sources. Never
overwrite a previous round's page, because it is the record of that pick.

- **Tokens first:** one custom-property set on the app root, `body.dark`
  flips it. Copy the colours the directions round fixed, then add the states a
  full app needs and the directions never showed: soft tints for the selected
  row and for "needs you", a green for success, a red for a destructive or
  armed action.
- **Real media and state colour, no more grey.** Show each screen in its most
  informative state, plus one transient state the eye would otherwise never
  see: a destructive button's armed second click, or the empty library chip on
  first launch.
- **CLI tags stay, hidden by default.** A "Show commands" toggle
  (`body.cmds .cmd{display:inline}`) keeps the rule-proof available without
  cluttering the look being judged.
- **Re-read the real JS for every label and threshold before drawing.** Pills
  and meters must match the app's own buckets (for example the count
  cut-offs for a "weak" badge). A radio or option list must show which option is
  selected in a way that is consistent with the counts next to it.
- **Say what moved on the page.** Any layout change against an earlier pick
  (buttons moved beside the preview) goes in that screen's label with the reason.
  The owner should never find a change by comparing pages.
- **Picks:** (1) overall yes / almost (note) / no; then one question per
  default the earlier rounds carried along unpicked (a side panel vs a
  separate page, a second colour vs one colour, a column that needs a CLI
  field first). Recommended option first, and name the CLI cost where there
  is one. Then a note box that asks to name the screen.

**When the owner's note opens NEW scope (e.g. "should it have Settings?"), do not
fold it into the locked picks or re-ask them.** Record the round's picks as
locked, then:

1. Grep the CLI's argparse flags and config/Settings class first, so the answer
   lists only what can actually be set. Nothing gets invented.
2. Answer in the chat with one table: candidate setting | where it belongs |
   why. The sorting rule:
   - A standing preference users differ on (theme) goes behind a gear in the
     top bar, as a side sheet. It is not an extra tab.
   - A flag that applies to one run (`--dry-run`) sits on that screen,
     in an "Options" fold.
   - A measured threshold never becomes a slider. Say why on the panel itself.
   - Anything that needs new persisted state or a new command is labelled as a
     CLI change, never drawn as free.
3. Ask the shape with one clarify pick. Recommend "add it to this mockup, you
   glance, then the next step".
4. Copy the page to `mockup-round1.html` first, then add the new screen and
   controls in the same build script (a panel over the dimmed screen,
   `position:absolute` in the `.app`). Mark every new label NEW.
5. Replace the form with a round-2 form that states what is already locked and
   asks ONE pick plus a note. Name the defaults the new screen carries unpicked
   (e.g. whether the fold starts open, which keys are listed).

**A question another agent left open (e.g. the order of the art's workflow
image) is answered by reading that agent's artefact read-only** (its render
script's docstring, the image) and relating it to the map, not by guessing
what it asks.

## Motion round (redesign step 4)

Goal: the owner judges the few moves by FEEL, which no screenshot shows. So the
page is a working demo, not a picture.

1. **Inventory today's motion first.** `grep -n -E
   'transition|@keyframes|animation|hover|reduced-motion'` over the real app's
   CSS, and the JS that re-triggers classes (`classList.remove/add` with a
   reflow). The live app usually already moves a lot (screen slide-ups, springy
   pops, hover lifts, a running progress stripe) while the step-3 mockup has
   none. Unless those moves are picked, the restyle inherits them unchosen, so
   they get their own panel and pick.
2. **Reuse the locked mockup, never fork its look.** Guard the step-3 builder's
   write with `if __name__ == "__main__":` and import its `header()`/`font()`
   from a new `build_motion.py`. Keep motion rules in a separate `motion.css`
   loaded AFTER `mockup.css`. Prove the old builder still produces a
   byte-identical page (`md5sum` before/after its rebuild).
3. **Panel 1 is a working core-loop window**: a small queue of made-up items,
   real buttons AND the real keyboard shortcuts, the exact moves the roadmap names
   (an action lands, undo, badge counts), and "Start again". Controls on top:
   feel presets (e.g. a calm one, a livelier one with overshoot, Off),
   **Slow ×5** (so a short move can be watched), Dark. Drive every duration
   from one CSS variable (`--t`) set by JS, so presets are one line each.
4. **Panel 2 puts today's other moves beside a calm version**, one pair per
   move, each with a Replay button (re-add a `.play` class after a reflow).
   Hover pairs say "point at it".
5. **Picks:** (1) the feel of the named moves, the fastest calm option first
   with its reason ("you do this hundreds of times, so you wait on it every
   time"); (2) what happens to today's other moves (calm / keep / none). Add a
   note box. Always add a `prefers-reduced-motion` block that makes every move
   instant, and say so on the page.

CSS traps this round hit:

- **Prefix every new class.** `mockup.css` is loaded too, so a short name like
  `.n` or `.o` collides with an existing rule (a Setup step number drew a big
  circle inside the badge). Use `.bo`/`.bn`-style names, or grep the base CSS.
- **`[hidden]` loses to any `display:` rule.** An overlay with
  `display:flex` shows despite `hidden`: add `.x[hidden]{display:none}`.
- **A rolling counter must not change its box.** Stack the old and new digit
  in one grid cell (`display:inline-grid` + both children `grid-area:1/1`,
  `overflow:hidden`) and animate `translateY`. Absolute positioning or block
  stacking changes the pill's height mid-roll.

Verifying motion: see the coder role's local-web-ui pitfall "Verify an animation" (freeze a
frame deterministically, read state back through `location.hash`). Capture
mid-move frames from the `file://` build (fonts are embedded, so it renders
the same); still take the full-page shot through the Lavish session URL once.

## Lock step (redesign step 5)

Goal: the picked mockup's tokens and motion become the tracked house style
(DESIGN.md v2 + the house CSS). No Lavish round is needed: the look is
already picked, so the step is transcription plus a few terminal picks.

1. **Bring the UI worktree up to date first, then build there.** The tracked
   style files may differ between main and the UI worktree (fonts and images
   redrawn on main after the UI branch forked). `ls` the design folder and its
   `fonts/` in both. The order: `git merge main` INTO the UI branch, confirm
   the images and fonts now match main, and write the lock on the UI branch,
   where the restyle will consume it. Main stays untouched until the UI merge step.
2. **Inventory every consumer of the old style before rewriting it.** Use
   `git grep` for the file names, the old font names and the token prefix:
   the art render helper, the assets README, an SVG marks file, the style-sheet
   image. Rewriting DESIGN.md alone leaves these stating the
   old style. Each one is either updated in this step or named as the art
   session's job.
3. **Raw material:** the round CSS files (`mockup.css` tokens for light and
   dark, `motion.css` keyframes, `--t` and ease). Drop everything that is
   preview-only: `.force`, the reduced-motion banner, the presets not picked, the
   form, the page chrome.
4. **Measure WCAG contrast of every text token against every background it
   sits on** (bg, side, sunk, the soft tints), in both themes, before writing
   it down as normative. Use the relative-luminance formula in a scratch
   script. Mockup colours are picked by eye, and some fail 4.5:1 as small
   text (typically light-mode amber and grey on the tints, dark-mode blue as
   link text, white on a dark-mode red). The fix: **split fill and text
   tokens.** Fills and bars stay exactly as the owner saw them, and a deeper or
   lighter `*-text` shade is used only where the colour is text. Find the
   shade by scaling HLS lightness until the worst background passes. Ask the
   owner with the before and after hex values. Never silently change a locked colour.
5. **Ask in ONE terminal clarify call:** the contrast shades; lock or change
   each carried-along default from earlier rounds (named); and removal of
   assets nothing uses any more (the old fonts). Recommended option first. If
   the answer is "wait", stop and write nothing. If a later "go" answers only
   some of them, take the recommended option for the rest and label each one in
   the ROADMAP, the log and DESIGN.md as "decided by <role>, not picked,
   revisable in tokens.json". Never put the owner's name beside a choice
   they did not make.
6. **One token file is the source; everything else is generated.** Keep
   a `tokens.json` beside DESIGN.md (other agents read it, and nobody
   hand-copies values). The shape that works:
   - `tokens.json`: colours per theme with the same keys in light and dark,
     plus the images' palette under its own key; each font with its file,
     licence, weight axis and fallback; type, spacing, radii, sizes, shadow,
     motion durations. Every entry carries a `role`. Components name colour
     KEYS, and the generator emits `{colors.X}` plus a `-dark` twin, so the
     linter checks contrast in both themes.
   - A stdlib generator (`src/design_tokens.py`) rewrites only the CSS block
     between `/* tokens:begin */` and `/* tokens:end */`, and DESIGN.md's
     front matter. The hand-written CSS classes and the prose stay as they
     are. It needs a `--check` mode that exits 1 when either file is stale.
     Write with `newline="\n"` so a repo set to `eol=lf` does not churn. Emit
     YAML strings with `json.dumps` (safe for `#` hex values and negative
     `em`). A second run must report no change.
   - Dark theme twice: `:root[data-theme="dark"]` (forced from Settings) and
     `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) }`.
   - The art render helper reads its palette from the same file. Re-render
     the images and check `git status` shows them unchanged (byte-identical).
   - A test fails when the generated parts are stale, a hex is typed below
     `tokens:end`, `fonts/` and `tokens.json` disagree on the font list, or
     the reduce-motion rule is gone. Break each one on purpose, watch it go
     red, then restore it.
7. **House CSS conventions:** prefix every class (`.v-*`). Reduced motion
   sets `animation-duration: 1ms !important`, not `none`, because
   `animationend` must still fire for the JS that clears motion classes. A
   spinner always sits beside words, so it can stop without losing meaning.
8. **The style-sheet image becomes a screenshot of the REAL CSS**, not a
   drawing: a script writes a page that uses only the house classes, takes
   headless-Chrome shots in light and in dark (`--headless=new
   --force-device-scale-factor=1 --virtual-time-budget=3000
   --allow-file-access-from-files`, temp HTML next to the CSS, deleted in
   `finally`), and stacks them with Pillow. Zoom with vision `region` on the
   small parts (labels, buttons). It catches CSS bugs a lint cannot,
   such as a label wrapping for lack of `white-space: nowrap`.
9. Lint (`designmd lint`, see the bundled skill design-md: this role is created with
   `--no-skills`, so install it if you want it), fix, regenerate, and lint
   again until you get 0 errors and 0 warnings. Hover variants fail too: a
   dark-theme hover that is lighter than the base colour drops white text
   under 4.5:1. An `orphaned-tokens` warning on the hairline colour is fixed
   by a `divider` component, not by deleting the token. Then update each
   consumer from item 2, run the gates, and commit on the tree from item 1.
