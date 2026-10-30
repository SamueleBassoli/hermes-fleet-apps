# Releases, user updates, and compatibility testing (desktop app on GitHub)

The push itself, repo hygiene, renaming and the pre-release review live in
`git-remote-publishing`. This file covers what the app and the release process need.

## Decide the update path BEFORE the first public version
A version that ships without any update notice strands its users. Raise it when the
owner mentions publishing, before the first tag; it is the one allowed new feature
during polish (say so as an explicit exception).

Options (recommend B):
- A: none (users watch GitHub themselves; nobody does).
- B: a manual "Check for updates" button in Settings. Privacy-first: no request at
  start, no timer, nothing cached.
- C: automatic check at start, opt-in (each check shows GitHub the user's IP).
- D: auto-download + install: advise against (complex; an unsigned exe is blocked anyway).
In every case the user runs the new installer over the old one (data and settings stay).

## Card shape for option B
- Server: one endpoint asks `https://api.github.com/repos/<owner>/<repo>/releases/latest`
  (stdlib urllib, timeout ~10 s, `User-Agent: <App>/<version>`). Read ONLY `tag_name`;
  strip a leading `v`; compare as numeric tuples ("0.10.0" > "0.9.0").
- 404 (no release yet, or a private repo) must NOT say "You have the latest version": the
  app does not know that. Offline / timeout / rate limit / 5xx / bad JSON = one plain
  "Could not reach GitHub" line, the cause to the log.
- The link shown is built from the repo URL constant, never from the response.
- Button disabled while checking.
- Tests fake `urlopen` (newer, same, older, 404, timeout, 403, 500, bad JSON, odd tag)
  plus a test that opening Settings makes NO request.
- Docs that said "never goes online" must name the manual check.

## docs/RELEASING.md
Steps in order: bump the version in every file that holds it (grep the old number
first) → CHANGELOG `[Unreleased]` renamed to `[x.y.z] - date` + a new empty
`[Unreleased]` → tests + lint → build (installer + `.sha256`) → install over the previous
version yourself → commit, `git tag vX.Y.Z`, push with tags → GitHub Release with notes
from CHANGELOG, both files attached → press the old app's button, expect "available".
Rules to state in it:
- Tag = `v` + the exact version, or the check never sees it.
- Test builds = pre-releases: `releases/latest` ignores them, so users are not offered them.
- Saved-data changes: append a migration step (never edit an old one), new settings need
  a default, never rename the data folders.
- The build's install/uninstall test must never touch the owner's real install: give the
  build script an isolated mode that installs a QA copy (its own AppId and names, inside
  the build folder) and removes it in `finally`.

## Order before the first public push
1. A read-only product review of the whole repo as a stranger would meet it
   (`git-remote-publishing` → pre-release gate). The owner decides the open questions as
   one lettered list; the coordinator dispatches the fixes as coder + docs cards.
2. A friends' test BEFORE publishing when the app was tested on one machine only.
3. History scrub + GitHub settings + push, only with the owner's go.

## Uninstall that cannot delete foreign files
"Also delete downloaded data" must delete only files the app itself wrote: keep a list
file appended on every download, delete exactly those, never delete a whole folder. A
wizard folder pick that already holds other files gets an `<App>` subfolder inside it.
Test with decoy files of "another app" in the same folder.

## Before a GPU proof on the owner's PC
List running processes matching the app/engine names first: an app killed from the task
manager, or an agent's forgotten dev server, can leave an engine running for days. Kill
only processes that are provably ours (command line inside our install or scratch), and
tell the owner. Test accented and spaced paths once: a scratch home and data folders named
like `José Rossi`, inputs with accents + CJK; check database, files, log; delete.

## AI-generated marker
Where the law asks for it (e.g. EU AI Act art. 50), write an invisible standard tag on
every saved output: XMP `Iptc4xmpExt:DigitalSourceType` = `trainedAlgorithmicMedia`
(edits of a user photo: `compositeWithTrainedAlgorithmicMedia`) + `Software`, pixels
untouched, NO prompt/seed/path/date. First check whether the engine itself writes the
prompt into a file text chunk; strip it and test that no chunk contains prompt text.
Uploaded originals are never modified.

## Hardening worth copying for any Windows app with an unsigned helper
- Retry renames ~2 s (file) / ~10 s (folder) on access-denied/sharing errors (antivirus
  scanning a fresh file).
- Catch the "blocked by policy" errors at every helper process start and name the cause
  (Smart App Control, AppLocker, antivirus) in one sentence + an INSTALL section; never
  tell users to turn Smart App Control off lightly (it cannot be turned back on without
  resetting Windows).
- Log a non-zero helper exit as `0x%08X` and add the app log tail (paths scrubbed, no user
  content) to the diagnostic report.
- Confirm the pinned GPU engine covers every promised GPU generation
  (`scripts/cuda-archs.py`, or the engine's build file).

## "Can I test on other GPUs / OSes online?"
Answer from these facts, then recommend real machines from friends (free, real hardware):
- Notebook and rental GPU services are mostly Linux containers: a Windows installer cannot
  run there. Useful only for a Linux build.
- Windows + NVIDIA in the cloud = datacenter cards, paid, an account and a card from the
  owner, often a quota request first. Same architecture as a home card, not the same
  driver or OS.
- Browser/phone compatibility services do not cover GPU desktop apps.
- Free GitHub Actions Windows runners (public repo) have no GPU but are still worth it:
  the suite on a clean Windows, the installer build, the install/uninstall test, a release
  on tag. They prove install + start, never GPU work.
- Windows-on-Arm PCs are not covered by an x64 build. Write "64-bit (x64)" in
  Requirements and do not claim support.
