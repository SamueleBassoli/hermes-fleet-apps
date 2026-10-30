# Packaging a local web app for a non-technical Windows user

Third phase after engine and web UI (see SKILL.md "Legacy rewrite"). The end user
double-clicks one thing, the browser opens, and closing is as obvious as opening.
Everything below goes into the packaging brief.

## Split it in two legs on purpose
The runtime behaviour (leg 1) and the build toolchain (leg 2) each fill a coder
context; expect the compaction rule to stop the job between them. Write the brief so
leg 1 is committable on its own:
1. Runtime: single instance, idle exit, heartbeat, `/api/quit`, native error box,
   bundle-aware resource path, version.
2. Build: PyInstaller spec + script, icon, zip, real-exe verification, README/CHANGELOG.

## Runtime rules (leg 1)
- **Single instance**: instance id + port written to the app's data folder
  (`%APPDATA%\<App>\`); on start, `GET /api/health` on the recorded port — if it
  answers with our id, open the browser tab and exit. Closes the "second copy on the
  next port" hole.
- **Quit path, both**: a "Quit <App>" button in Settings (confirm if a job runs) AND
  auto-exit after N minutes with no page heartbeat and no job. Expose N via an env var
  (`<APP>_IDLE_SECONDS`) so the test does not wait 10 minutes. No tray icon required.
- **Errors before the browser opens** → a native message box
  (`ctypes.windll.user32.MessageBoxW`) in the user's language with the log path; a
  windowed exe that exits silently looks "broken".
- Static files resolved through a `sys._MEIPASS`-aware helper, never the cwd.
  Settings and log stay in the app's data folder.
- Version in ONE place (`<pkg>/__init__.py`), shown in Settings and in `/api/health`,
  used in the zip name.

## Build rules (leg 2)
- PyInstaller **one-dir**, windowed: one-file starts slowly and trips antivirus
  heuristics far more often. Zip the folder: `dist/<App>-<ver>-win64.zip`.
- PyInstaller only inside the project venv via `requirements-build.txt`.
- **The build script refuses to run with `PYTHONPATH`/`PYTHONHOME` set** (exit 2 with a
  plain message): PyInstaller bundles whatever it can import, so a build from a shell
  that exports another environment's site-packages silently ships unrelated libraries.
  A zip that grows by MBs between two commits that only removed code is the symptom.
- Tests compare against `<pkg>.__version__`, never a literal version string.
- Icon from the design folder's SVG → multi-size `.ico` (16/32/48/256).
- Verify the bundle contains fonts, strings, static files AND tkinter/tcl if a native
  folder picker is used.
- Scan the zip: no `venv/`, `tests/`, `.design/`, `_private/`, `.git`.

## Verification the brief must demand (from `dist/<App>/`, NOT the repo, `<APP>_HOME` → scratch)
1. Launch → browser opens, `/api/health` reports version + bundled flag, time to first
   200 recorded.
2. Launch again → no second server, same tab target.
3. Use the folder picker once.
4. Settings → Quit → process gone, port closed.
5. Idle exit with the env var shortened.
6. Zip size + cold start recorded in the LOG.

## The coordinator's own spot-check before handing the zip over (5 minutes)
- Unzip into your scratch dir. On Windows under an MSYS shell, give the exe
  Windows-form paths (`C:/...`): a `/tmp/...` value is a different folder for a native
  program, and the cleanup misses one.
- Start with a `--no-browser` flag so no tab pops on the owner's screen; read port +
  instance id from the instance file.
- A second launch must print "already running" and exit 0 in well under a second;
  `netstat` shows ONE listener.
- Quit via the API (send the `Origin` header the origin gate expects), then the
  instance file is gone and no process is left. Delete the folder only after a short
  pause — the exiting process still holds it.
- A from-source copy the owner runs on another port is theirs: report it, never kill it.

## After handover: dropping the legacy interface
When the owner asks to remove the old CLI (nobody uses it): `git rm` the v1 files, the
old CLI and its tests, the v1-only requirements; point `python -m <pkg>` and
`[project.scripts]` at the web launcher; remove README sections about the old program;
a CHANGELOG "Removed" entry; patch version bump; tests; clean rebuild; live health/quit
spot-check; delete the superseded zip. Say that v1 stays reachable at its baseline
commit.

## Handover words for the end user
1. Unzip anywhere, double-click `<App>.exe`.
2. The first time, SmartScreen may say "Windows protected your PC" → "More info" → "Run
   anyway" (unsigned exe, normal; say it in plain words, no scare).
3. The browser opens on a local page; nothing leaves the PC except what the app is
   meant to download.
4. Close it from Settings, or it closes itself after N minutes idle.
