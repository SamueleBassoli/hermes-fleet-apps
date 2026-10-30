# Read-only rule-drift audit

A brief that says "find every rule the app decides differently in two places,
or documents differently from what the code does; write findings to a private
file; do not fix". A product rule is anything the app decides for the user:
what gets learned, what counts as unknown, what is undoable, what a number
threshold is.

## Procedure

1. Load every tracked text file (code, UI js/html, docs, AGENTS.md, the
   agent SKILL.md) into the execute_code kernel ONCE, with `show`/`find`
   plus a regex `grep(pat, files)` that prints `path:line: text`.
2. Grep every config constant by name across src, UI and docs in one call.
   For each constant, the drifts are: a caller that ignores it, a hard-coded
   copy of its value in the UI, and a doc that quotes an old value.
3. For each user action, list every door that performs it (CLI command,
   desktop Api method, page handler, browser page) and compare four things:
   - the gate (minimum, cap, filter)
   - the stale-plan check (does Go run only what the preview showed?)
   - Undo
   - the words shown to the user
4. Do the same for the outcome vocabulary. Map each internal verdict to the
   word each surface prints (CLI text, the plain-words map in the Api, the
   map in the page, the docs). Two verdicts that share one word, or one count
   that two lists disagree on, is a finding.
5. Check each input type the app accepts (for example image vs video, small
   vs large files), empty/first-run states (does a CLI error that says
   "run 'x' first" reach the window verbatim?), dead names, and bridge
   allow-lists vs documented flags.
6. Before writing, re-`show` every file:line you will cite, in one cell.
   Line numbers recalled from earlier output are wrong often enough to
   matter, especially across a context compaction.

## Output shape

One entry per finding:

- a plain-words title
- where: file:line for EACH side
- what each side does
- how the owner would notice it in the window (a concrete click and what
  they see)
- severity: wrong result / confusing / cosmetic
- one-line proposed rule, no code

Sort the entries by severity, end with a 5-line summary, and report in chat
in the number of lines the brief names. Then stop, without fixing anything.

## Findings that recur (check these first)

- Two doors to the same action with different gates (min count, cap, a
  filter one door applies and the other skips).
- An old rule surviving in review UI text or docs after the code moved to a
  new one.
- A plan-first guard on some Go buttons but not all.
- Undo offered on one path of an action only.
- UI copy promising a ranking ("best first") the code does not do (file order).
- UI numbers typed by hand instead of read from the engine.
