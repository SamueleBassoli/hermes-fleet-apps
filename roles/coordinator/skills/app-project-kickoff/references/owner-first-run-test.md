# Owner first-run test (pre-release polish)

For a product meant for GitHub, a polished app + a clear README beat a trailer. Polish =
change or remove only, no new features.

## Prepare
- Truly fresh state: stop your own dev servers (find the PID on the port, check its
  command line, stop it, re-check), confirm no install and no leftover app data.
- Before the installer build, grep the app for `placeholder` assets (icons, strings): a
  first-day placeholder window icon survives to the shipped exe because tests and reviews
  never look at the title bar.
- Rebuild the installer from current main with the repo's build script.
- Open a findings file (table: N | where | problem | wanted | cause | note) + a
  CHECKLIST line.
- Give the owner numbered steps (installer path, SmartScreen "More info → Run anyway",
  defaults, first-run wizard, first real use, then each screen); ask for one screenshot +
  one line per issue.

## Per screenshot
- Verify its facts against the machine yourself (GPU, RAM, versions) before answering.
- Answer the owner's point, then at most 2 polish observations of your own as "decide if
  you want them"; log only what they approve; repeat the running numbered list in every
  reply.
- A bug ("can't scroll"): find the cause in code (file:line in the row), give a
  workaround for the rest of the test, add a regression-test idea to the fix.
- "X does nothing": read the code first. Often it works but gives no feedback: explain
  how to try it, log only the missing feedback.
- The same defect on a second screen = the SAME row widened to "fix app-wide" with a
  grep hint.
- A number that disagrees with a control: "verify first", with the likely innocent cause;
  a later screenshot or the stored request clears it.
- A request only possible via a workaround gets one mention with its caveat; on "not now"
  mark the row dropped, never re-propose it.
- "Screen X is slow the FIRST time, instant after": list the calls that screen awaits
  before drawing, time each cold then warm against the built app on a scratch home. A call
  that shells out to an external CLI is the usual culprit. Fix direction: draw the page at
  once and fill only the slow row when it answers (neutral state meanwhile); never cache
  it, or the row goes stale. Report before/after ms and say where it was measured.
- "Did not show after uninstall + reinstall": read the uninstaller first. Settings kept by
  design make an install over kept data act as an update. Gate first-run steps on disk
  state (is the required data there?), not only on a "first run done" flag.
- "Are downloads parallel?": answer from the code, then compare the measured speed with
  the user's line: at the line's cap, parallel gains nothing.
- Output-quality complaints: look at the ORIGINAL file at 1:1 and measure before
  answering; list suspects as unproven; change a default only on a fixed-seed A/B run in a
  scratch home.
- A label that contradicts what the owner just used (a "v2" badge on a working feature):
  offer remove-badge vs hide-feature, recommend the one matching reality.
- Feature ideas raised mid-test: park them in CHECKLIST `## Later` with their
  precondition; never in the fix batch.

## UI pitfalls these tests surface (put them in the coder brief)
- In a `100vh; overflow:hidden` shell every screen's `<main>` needs its own scroll
  container; test that each screen scrolls.
- Selection/hover rings drawn as OUTER box-shadow are clipped by sticky headers and
  overflow strips: draw rings inset, app-wide.
- A live meter refreshed only at start-up looks frozen during work: poll while work
  runs, never idle.
- A queue shown only as a 3 s toast is invisible: every queued job needs a row with
  cancel.
- An SVG with fixed width/height and no `viewBox` is cropped by a smaller
  `overflow:hidden` box; a QR code also needs a quiet zone of 4 modules — scan it with a
  real phone.
- Support/contact texts written before the publishing channel was known → the repo's
  Issues/Releases pages, ONE URL constant, the owner confirms the URL before the push.

## Fix batch
- One coder round for the whole list: cards of ~3 rows each by area, one worktree +
  branch per card, in parallel (`fleet-project-pipeline`).
- Name rows by the FILE's row numbers, not the chat list's; paste each row's wanted fix
  and the owner's rule into the card.
- Gate each branch (suite + lint), merge one by one, rebuild, hand back to the owner.
- Per finished leg: read the worker's REPORT and the risky diff, look at its proof shots
  (say if they come from a test page — the owner's real window is the final check),
  delete the shots, merge, remove worktree + branch. Then one short ✅ message per leg:
  what the owner will see, the test count, what was NOT checked.
- Worker follow-ups are the owner's one-line yes/no questions, each phrased as what they
  would see or do, never as a CSS or accessibility term. When the owner answers "use best
  practice", decide, state the decision + a one-clause why, and log it. A fix that would
  need a new piece of UI is a feature: ask, do not slip it in.
- A fix that reuses a shared string/helper can silently drop words the old screen had:
  read the diff for removed UI text and list it as a "check this when you reinstall" line.
- Start the installer rebuild in the same turn as the last merge (background, notify).

## Round 2
- Log new findings under `## Round 2` in the same file, continuing the row numbers; do NOT
  dispatch per finding. Wait for the owner's go: one coder round, one rebuild, one
  reinstall.
- A word that means two things in UI terms ("full screen" = maximised vs true
  fullscreen) gets a two-option plain explanation before logging; recommend one, log it
  "owner to confirm".
- Round-2 cards: same shape, own worktree off current main, body says "read ONLY section
  Round 2 and after" so workers do not redo round-1 rows.
