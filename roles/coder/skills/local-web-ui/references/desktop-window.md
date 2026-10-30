# Desktop window (pywebview): when the page graduates to an app

Use this when non-technical users must run the tool without a terminal, or when the page
needs a real folder path or live progress. A browser tab can do neither: it cannot return
a real filesystem path from a folder picker, and without JS it only updates on a click.

## Why pywebview over the alternatives

| Option    | Cost                                                        |
|-----------|-------------------------------------------------------------|
| pywebview | wraps the existing HTML/CSS, stays all-Python, native folder dialog, OS webview (WebView2 on Windows, WKWebView on macOS, GTK/Qt on Linux) |
| Electron  | a second runtime (Node) plus about 150 MB of bundled Chromium |
| Tauri     | Rust toolchain plus a Python sidecar for the engine          |
| Qt        | rewrite the page as widgets                                  |

The real cost of any desktop app is PACKAGING: one installer per OS carrying Python and
every runtime dependency. Recommend one OS first and add installers later.

## Shape

```
src/<pkg>/desktop/
  __main__.py      python -m <pkg>.desktop [--data-dir <dir>]
  app.py           Api class (js_api) + worker thread + webview.start
  bridge.py        the only road into the tool
  ui/index.html    CSP meta, <script src="app.js" defer>, <link app.css>
  ui/app.js        listens to pywebview.state; textContent only
  ui/app.css       motion, with a prefers-reduced-motion off switch
```

- **`bridge.py` is the window's only road into the tool.** `run(data_dir, command,
  *args)` calls `cli.main(["--data-dir", d, "--json", command, ...])` in-process with
  stdout/stderr captured, parses the one JSON document, and returns
  `{ok, code, data, error}`. Catch `SystemExit` so argparse errors become messages. An
  ALLOWED map (command -> permitted flags) refuses anything the window has no screen for;
  `--data-dir` always comes from the app, never the page. A module-level Lock serialises
  calls because `redirect_stdout` is process-wide. Test the allow-list, the flag check,
  the error dict and the lock, and sabotage each.
- **Widening a command's allowed flags: pin every flag that must STAY out, each alone.**
  A refusal test that sends two forbidden flags together still passes when one slips into
  the allow-list. Add each as its own case, mixed into an allowed call and in
  `--flag=value` form.
- A live screen needs a CLI mode that streams progress (`--progress`, see SKILL.md). Do
  not loop the engine yourself to get progress: a second loop drifts from the real one.
- Pin pywebview as an optional extra (`desktop = ["pywebview==X.Y.Z"]`). The CLI install
  stays free of GUI dependencies.
- `webview.create_window(title, str(UI/"index.html"), js_api=api)` then
  `webview.start(http_server=True, private_mode=True)`. pywebview serves the ui folder from
  its own local server, so `script-src 'self'` covers `app.js`.
- Native folder picker: `window.create_file_dialog(webview.FileDialog.FOLDER)` returns a
  tuple of real paths, or None if cancelled. Validate `is_dir()` on the Python side.
- **Live updates: `window.state`.** Assigning `window.state.key = value` from a worker
  thread fires a `change` event in JS. Reassign a whole dict each time: object mutations
  are NOT detected. No polling, no websocket.
- Heavy work runs in a `threading.Thread(daemon=True)` guarded by a non-blocking Lock, so a
  second click returns "already running" instead of racing.
- Thumbnails: resize and encode in memory into a `data:image/jpeg;base64,` URL; the CSP
  needs `img-src 'self' data:`.
- Wait for the `pywebviewready` event before calling `window.pywebview.api.*`.
- Script lockdown terms (state them in the project's instruction file): own files only, no
  remote URL, no inline script or `on*=`, no `eval`, CSP `'self'`, user strings set via
  `textContent`. Before committing, grep the ui folder for
  `innerHTML|eval(|new Function|http`.

## The mirror check (UI only through the CLI)

The Api class is presentation only. Enforce it with a check over `desktop/` that fails on:
importing store/engine/file-moving modules, `sqlite3` or `shutil`; any `unlink`, `rename`,
`rmtree`, `os.remove`; any use of `cli` other than `bridge.py` calling `cli.main`. Then
replace each bypass with its CLI-first form:

| Bypass in the window              | CLI-first form                                   |
|-----------------------------------|--------------------------------------------------|
| reads folder layout via internals | a `folders <root> --json` command                |
| its own preview loop              | the real command with `--progress`               |
| reads stored records from the DB  | a list command whose `--json` emits the field    |
| reads run journals from disk      | `runs --json`                                    |
| deletes a user's file on click    | "Open folder" (reveal in the file manager); the human deletes |

- **Thumbnails only for paths a command just returned.** Keep the set from the last
  command output and refuse any other path, so the page cannot read a file by naming it.
- A checker that finds its repo root from its own file location checks the MAIN checkout
  when run against a worktree, and reports green on code it never read. Give it a root
  override (`<APP>_CHECK_ROOT`) and pass a native path, not a git-bash `/c/...` path.
- Destructive commands with plan-then-`--apply` map to a two-step confirm: show the plan
  (with the NAME it resolved to), then apply. No undo = say so on the confirm.
- **Apply runs only the plan the human saw, enforced in the Api, not the page.** On a
  successful preview store a fingerprint: the exact args plus a change counter. Bump the
  counter in the Api's single run wrapper on every OK write or undo; a failed command does
  not bump it. `--apply` refuses with "preview again" when there is no plan, the options
  differ, or the counter moved; a spent plan is cleared. The page greys the old plan, but
  the Api refusal is the guarantee.

## A queue screen (answer waiting items one at a time)

Only after the CLI has a door for the answer (`agent-facing-cli`, "Giving a UI-only action
a CLI door") and the bridge allows it.

- **The Api remembers the list the last `<list> --json` returned, keyed by resolved path,
  and answers only those.** Build the answer command from the path IN THAT LIST, never
  from the string the page sent. Drop an item only when the answer consumed it.
- Mirror the page's card rules in JS (one question in words, answers first, Skip). A
  refusal shows on the same card with every control kept. After an answer, one line under
  the card: what happened and an Undo button calling the existing undo command.
- Link it from the screen before it ("N wait for you") and badge its tab.
- **Overlays in `%` need a frame that is exactly the picture.** Either shrink-wrap
  (`max-height` on the `<img>`, frame `position: relative; line-height: 0`), or, to fill a
  column, make the stage a size container and give the frame the item's own aspect ratio
  from the JSON before the picture loads. A frame with its own height and
  `object-fit: contain` letterboxes the image and every box drifts. Measure over CDP: each
  box rect equals its stored box scaled by `img.width / item.width`.

## Naming items one at a time (a grid plus a large viewer)

- **Reuse the screen's existing large viewer; never add a second overlay.** The one overlay
  already sits under the job lock.
- **Grid tile: a click on the picture opens it large; only the tick box ticks.** A real
  button (`role=checkbox`, `aria-checked`), click does not bubble.
- **One action path for the grid and the viewer.** A test counts calls to the action API so
  a copy cannot appear.
- **Arrow keys yield to a text box that has text.** Prove it over CDP: type, press ←, read
  the caret position and the item counter.
- **After the last item, show an "All done" state** with a button back to the list. Never
  close back to the grid on its own: the human wants to see that the job finished.
- **A grid-size slider picks the COLUMN COUNT, never a tile width.** With `auto-fill` a
  width only shows when it changes the column count, leaving dead zones on the bar. Use
  `repeat(var(--cols, N), minmax(0, 1fr))`, `step="1"`, a `<datalist>` for notches. Right
  = bigger: map value to columns in the page, never `dir="rtl"`.
- **Size thumbnails from a measured grid width** at the target screen widths; a smaller cap
  leaves big tiles as upscaled blur.
- **A long list gets type-to-filter on the EXISTING text box.** Accent- and case-blind
  tiers: exact, prefix, word-prefix, contains, then one edit off under a separate "close:"
  line from 3 letters. Enter picks only a highlighted row. The go button names the
  HIGHLIGHTED row, not the typed text; print its label after each key step in the driver.
- **Put page logic worth testing in its own pure `.js` file and test it through `node`
  from pytest.** End the file with `if (typeof module !== "undefined") module.exports =
  {...}`, pass input as JSON on stdin, `skipif(shutil.which("node") is None)`. Load it
  before `app.js`; plain scripts share one global scope, so grep for name clashes.
- **Check that a setting really persists before promising it.** A `private_mode=True`
  window keeps no localStorage between launches; a remembered setting needs its own file
  (SKILL.md, window preferences).
- CDP `Runtime.evaluate` calls share one global scope: wrap multi-statement evals in
  `(() => { ... })()`.

## A full plan view (every item, grouped, before "for real")

- Build it from the CLI's own plan JSON. Every item a count card counts has a tile; items
  with no single destination get one plain line, never a group. The go button counts only
  real changes.
- Group by destination, biggest first, then the will-ask group, then stay-put groups folded
  in `<details>` (fill a folded grid only on `toggle`). Cap each group (~12) with "Show
  all N".
- Hundreds of items stay fast: empty tiles plus an `IntersectionObserver` for thumbnails;
  reuse thumbnails already made during the run.
- Show folders relative to the root the CLI RESOLVED (returned by the Api), not the path
  the page holds: through a mapped drive or symlink the prefixes never match and every
  header shows a long private path.
- Click = one item large (what, where it goes, why in words), arrows step, Esc closes.

## Styling: design is its own phase, and the owner decides it

- Before adding or extending ANY screen, read the project log for the design status. While
  the look is "not final", say so in the plan BEFORE building ("logic now, look stays
  provisional"), not after screenshots in the wrong style.
- A chosen prototype is the spec (`decision-forms`, "Prototyping a UI"). Port its look only
  after it is chosen. Do not restyle from a style sheet on your own initiative.
- Load the design tokens file; do not copy values by hand. Every bundled font needs its
  licence file before shipping.

## Data safety in a spike

A "preview" that reuses the engine's decide-function may still WRITE (indexing unseen files,
for example). Read the function before calling it a dry run. Point the spike at a COPY of
the data (`--data-dir <scratch copy>`) and name the copy's location in the handover.

## Verify it

- **Never touch the owner's real data.** Tests that exercise the default data folder point
  the OS data variables (`LOCALAPPDATA`, `XDG_DATA_HOME`, `HOME`, `USERPROFILE`) at a
  temp folder and ASSERT the resolved folder is inside it before anything runs. Stub
  `webview.create_window`/`start` to record the Api instead of opening a window. Record
  size + mtime of every candidate real store before and after a window run; which one is
  real comes from the project's instruction file (`production-install`, "Which store is
  the REAL one").
- An env var (e.g. `APP_DEBUG_PORT`) sets `webview.settings["REMOTE_DEBUGGING_PORT"]`,
  with `debug=True`. The window then answers CDP like Chrome, so `scripts/cdp_shot.py`-
  style driving works unchanged. Poll `/json` for the `page` target.
- Launch the app as a background process, drive it from a second process, kill it after.
  Check first for a copy the user already has open; leave theirs alone and use your own
  debug port.
- **Blur every picture before a shot you will look at** when the content is personal. The
  CSP blocks an injected `<style>`, so add a constructable sheet over CDP
  (`new CSSStyleSheet()`, `replaceSync('img, canvas { filter: blur(14px) !important }')`,
  append to `document.adoptedStyleSheets`), include classes that paint pictures as
  backgrounds, and assert a `blurred` flag before EACH capture.
- A native dialog cannot be clicked over CDP. Replace only the dialog call in the driver
  (queue paths); every other call stays the real API. Say the picker click was not
  exercised.
- Write every CDP wait predicate as a boolean and give every wait a timeout that raises
  with its label.
- **Prefer a fresh app over `Page.reload` after a UI edit.** A reload can leave
  `pywebview.state` un-injected and drops session state, so the shot shows a state the
  human never sees.
- **Type and press keys like a hand:** `Input.insertText`, `Input.dispatchKeyEvent` with
  `key`, `code` and `windowsVirtualKeyCode`. Setting `.value` from JS skips listeners.
- **Prove a lock with TRUSTED input**, not `element.click()`: `Input.dispatchMouseEvent` at
  the element's rect centre (scroll it into view first) and Tab key events.
- **Scope driver selectors by element or id.** A state class on `body` matches every
  `closest()` check.
- **Seed a shot world through the CLI, not the window**, when a job is only the backdrop.
- **Put fixtures in the state the real pipeline leaves them**, with distinct content when
  the tool deduplicates by hash.
- **Tear down by command line, not by port.** A venv `python` is often a launcher stub that
  starts the real interpreter as a child; killing the port's PID can leave a process
  holding the scratch data. Find every process whose command line contains the scratch
  data dir and stop each, then delete the world. A process query matches itself; filter by
  process name. If you started the app with a background-process handle, stop it through
  that handle.
- Build each re-run's world in a NEW scratch folder rather than deleting the old one
  mid-run; put every kill and delete into one command at handover and say it will ask for
  approval.
- Say which outcome paths the fixture never exercised.
- Keep the world builder and the driver in the project's spikes folder before emptying
  scratch: the next screen reuses both.
