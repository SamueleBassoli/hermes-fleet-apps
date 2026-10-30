---
name: context-acquisition
description: "Use when a session starts from a handoff brief. Read once."
version: 1.1.0
author: coder role of hermes-fleet-apps
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [context, onboarding, handoff, reading, verification]
    related_skills: [handoff, build-method, project-memory]
---

# Context Acquisition

The receiving half of a handoff. The owner may end a session on purpose and start a fresh
one, pasting a brief that says: read these files, verify every claim, then wait.
This skill is how that pass is run so it finishes in one sweep instead of five.

The `handoff` skill owns how a brief is WRITTEN. This owns what to do when one
arrives.

## The pass, in order

```
  1. VERIFY TREE   one read-only command, before reading anything
  2. READ ONCE     the listed files, in the listed order, tracked
  3. CHECK CLAIMS  the brief's numbers against what the command printed
  4. REPLY         what was read, what was verified, what was NOT started
```

## 0. Batch the whole pass into three turns

Every read in the brief is independent, so they go out together, never one
per turn — each extra round-trip resends the whole conversation:

```
  turn 1   tree command  +  skill_view(context-acquisition)
  turn 2   every listed file/slice  +  grep -nF for the log headings
  turn 3   EVERY gate the brief lists  +  a cheap look at any artefact
           the brief makes claims about (ls the dir, cat the config)
```

The tree command can absorb the artefact checks too: chain the backup copy's
`git -C <backup> log --oneline -1`, `git check-ignore -v <private files>` and
`ls` of the data dir onto it, so one call proves the whole "state" paragraph.

**Verify "empty" by counting, never by a top-level `ls`.** `find <dir> -type f
| wc -l` plus per-subfolder counts. A dataset dir the brief calls empty can
hold folders the user filled by hand after the brief was written, and
the next step's contract ("destination already exists?") depends on it.

**A real-data reference check covers the db AND its `-wal`/`-shm`.** `ls -la`
all three, with `stat -c '%y %n'` for exact times. If the main file matches the
brief but the `-wal` is dated after the reference, something wrote after it.
A newer `-shm` alone (db size/date unchanged, `-wal` 0 bytes) means only that
something OPENED the database: a reader, not a write. Report it as such, not as
a change. Either way check the user's own processes (`pythonw.exe` AND
`python.exe`) and report it to the owner as a question, never as yours. Never kill those processes.
On Windows under git-bash use `tasklist /FI "IMAGENAME eq pythonw.exe" /FO CSV
/NH` with SINGLE slashes: MSYS path conversion is off here, so `//FI` is passed
through as written and rejected.

**Inspecting a user's REAL database is not free of side effects.** Opening a
WAL-mode SQLite file, even with `?mode=ro`, creates `-shm`/`-wal` beside it.
Prefer `file:<db>?immutable=1` when no `-wal` file exists yet (ls first).
When a `-wal` exists, `immutable=1` silently ignores its content: copy the
db, `-wal` and `-shm` together into scratch, count on the copy, delete the
copy afterwards, and `ls -la` the originals to show sizes and mtimes did not
move. Report both.

Run EVERY gate the brief names (pytest, check.py, a sabotage harness...)
inside the pass, not after it: they are read-only, the reply must quote their
real numbers, and a gate that is already red changes what "wait" means. Chain
them with `;` (not `&&`, so one red gate still reports the rest), each
`| tail -3`, one call for all totals. Keep the terminal timeout at or under
600 s: a higher value silently turns the call into a background process, and
then the totals only arrive through `process_manage wait` (itself clamped to
180 s, so poll again). A foreground call is also cut at ~420 s whatever its
timeout says, so a fixed wait for a background job is `sleep 400` with timeout
410, repeated, never `sleep 580`. **Run each worktree's gates with THAT
worktree's own interpreter** (`cd <wt> && ./.venv/Scripts/python.exe -m
pytest -q`, `.venv/bin/python` off Windows), and `ls -d <wt>/.venv` in the
tree command first. A runner wrapper (`uv run --frozen`) assumes a lockfile
the repo may not have, and one venv shared across worktrees tests the wrong
source tree. **A gitignored gate script (`_private/.../check.py`) exists only
in the main folder, never in a worktree** (ignored files are not checked out):
run it from main's copy with the worktree's interpreter and the script's own
root switch (grep the script for `environ`/`ROOT` to find it, e.g.
`<APP>_CHECK_ROOT=<wt>`). Without the switch it silently checks main's tree
and reports main's number for the worktree. **When the brief names a gate by filename only** ("node --check app.js"),
locate it with `search_files target=files` in turn 1, never guess the path:
a guessed path fails as MODULE_NOT_FOUND and costs a round-trip. Put the real
path in the reply so the next brief carries it. Append the read-only DB count script to the same chain
so the database numbers arrive with the gates. When a total differs
from the log's by an amount the log itself explains ("70/70 before X was
added"), report both and say why — do not flag it as drift.

## 1. Verify the tree first, in ONE command

Structural claims are one call, not four:

```bash
git status --porcelain && git log --oneline | wc -l && git ls-files | wc -l && git stash list
```

Silence from `status --porcelain` and `stash list` IS the clean-tree proof — say
so explicitly rather than reporting "no output". Run this before the reading,
not after: if the tree is dirty when the brief says clean, the reading order
changes.

**When the repo has several worktrees/branches, verify EVERY HEAD the brief
names, not just the one you work on.** Chain `git worktree list` and
`git -C <main> log --oneline -8 --format='%h %ad %s'` onto the tree command.
Another worktree (or another agent) can merge into main between the moment the
state was captured and the brief was written, so the brief's "main @ X, N
ahead" can be stale even when the timestamps look safe. Report the new commits
by subject, and flag any that contradict a decision the brief records (a style
"not adopted" that is now merged on main) as a question for the owner, never a fix.
Check the backup copy's HEAD for every branch too: it lags a merge made
outside the session.

**Never derive a count by arithmetic from the brief.** Commit counts and file
counts are what the command printed. A version line computed instead of run is
the single most repeated error in this kind of work. "N ahead of GitHub" is
`git rev-list --count origin/main..main` (or the `[ahead N]` of
`git status -sb`) — against the last FETCHED remote, so say so, and do not
fetch during a read-only pass. Briefs get this number wrong often; a mismatch
goes at the top of the reply, stated as "brief says X, git says Y".

**Check that every folder the next step writes INTO exists** (a prototypes
dir, an output subfolder). A brief saying "prototypes live in X/ui/" can
describe the plan, not the disk; report "not created yet" rather than
letting the first write discover it.

## 2. Read each file ONCE, and track what landed

Keep a running list: file → surfaced / not surfaced. A file whose body you have
actually seen is done. Without that list the same document gets fetched three
and four times, each pass burning the context the reading exists to build — and
the brief's own file list reads as unfinished work forever.

Order matters: read in the order the brief gives, because it is ordered by what
the next file assumes.

To locate a log entry by its heading, use `grep -nF '## [date] build | x.N' file`
(fixed-string) and read from that line — a regex search tool parses the
`[2026-01-31]` in the heading as a character class and errors out.

**Fastest shape when the brief lists slices ("cli.py ~678–880", "from heading
X to heading Y"): load every file into the execute_code kernel ONCE, locate
the anchors by plain substring, then print ranges.** One call gets the line
count of every file plus the real line numbers of every anchor, which also
checks the brief's "~line N" claims. The kernel keeps the text, so each later
slice costs nothing:

```python
out = {p: (R/p).read_text(encoding="utf-8").splitlines() for p in files}
find = lambda p, s: [i+1 for i, l in enumerate(out[p]) if s in l]   # anchors
show = lambda p, a, b: print("\n".join(f"{i}|{out[p][i-1]}" for i in range(a, b+1)))
```

Plain `in` is fixed-string, so bracketed log headings need no escaping. Widen
each code slice by ~10–40 lines past the named function to include its CALLER
— see section 4.

**The kernel can restart between ANY two cells and drop every variable**, even
in the middle of a read-only pass. Open every cell with the three lines
above (repo path, `out`, `find`, `show`): re-loading the text is cheaper than
the round-trip a `NameError` costs. A `NameError` in a write cell happens
before anything is written, so re-run the whole cell. Never patch it up
piecemeal.

**Verify line-ending claims on raw bytes, never with a text-mode tool.**
`b = path.read_bytes(); b.count(b"\r\n"), b.count(b"\n")`. Equal counts mean
CRLF, zero CRLF means LF. `grep -c $'\r$'` under git-bash reported LF files
as fully CRLF, and a wrong verdict here corrupts every later find/replace.
`git ls-files --eol` can list `i/lf w/crlf` files while `git status` is clean.
That is an old checkout, normalised on commit, and it is not drift. Take the
baseline count during the pass and report it once. After each edit, check only
the files the step touched; a whole-tree check then flags only what you changed.

## 3. When a read produces no visible body, change METHOD

An identical call returns identical nothing. Two empty results is the signal to
switch, not to try a third time. Escalate:

1. chunk the same reader with `offset` / `limit`
2. read the bytes directly and print them yourself:

```python
import pathlib
t = pathlib.Path(r"C:/path/to/file.md").read_text(encoding="utf-8")
print(len(t))
print(t[:13000])      # then t[13000:26000], etc.
```

Print in slices of roughly 13k characters. A single print of a 40k-character
document is far more likely to be dropped by the output layer than three
prints of 13k, and the slice boundaries make it obvious which part is missing.

For line-numbered code, slice the list and number it yourself:

```python
lines = t.splitlines()
print("\n".join(f"{i}|{l}" for i, l in enumerate(lines[:300], 1)))
```

Say in the final reply which method actually produced the text. A future session
reading the same repo should not rediscover it.

## 4. The reply IS the deliverable

"Read, verify, then wait" ends in a message, not in a last file read. Reading is
not progress until the acknowledgement exists. It states:

- which files were read, with sizes or line counts as evidence
- what was verified **by running it**, with the actual output — tree,
  both gates, and the on-disk shape of any artefact the brief describes
- where a dated log entry contradicts a later correction, say the earlier
  one is correct AS HISTORY and name the entry that supersedes it — never
  propose fixing an append-only log
- which of the brief's claims the files confirmed
- explicitly: the next step has NOT been started
- **gaps in the NEXT step's plan that the code shows**, found by reading the
  CALLERS of every function the plan changes, not just the functions it
  names. A plan that widens a guard or adds a new case to an enum usually
  misses a sibling check next to the call site (a second set that must gain
  the new case, an early return still keyed on the old case only) and a
  docstring that promises "until step N". List them as additions to the plan.
  Do not act on them. More shapes to check every time:
  - **A new skip/refuse reason needs a slot in the REPORT.** If the summary
    line and the `--json` payload only know the old reasons, the skipped item
    vanishes silently — the very failure a guard exists to stop.
  - **A new guard can contradict a settled design rule** ("use the largest
    item" vs "refuse inputs that hold several items"). Name the rule it carves an
    exception from, so the docs change with the code.
  - **A separation that rests on a wrapper** (launcher, alias, flag) — grep
    for any OTHER way in (env var, config file, default path). If there is
    none, the bare command silently hits the default store; say so.
  - **A new operation KIND through an existing journal/undo path** (copy
    where the writer only knew move, delete where it only knew rename).
    Read the undo/reverse function: it usually assumes the old kind and
    will fail or do the wrong thing on the new one (undo of a copy "moves
    back" onto an occupied original). The journal must record the kind.
  - **A new command that re-applies an existing filter** ("single-item
    input", "usable sample") must CALL the existing definition, not restate it. Two
    copies drift, and the new command then produces input the old one
    refuses. Name the function to share.
  - **A present-tense doc whose intro predates the spike** (roadmap phase
    header still stating the pre-measurement numbers or rule). List it as
    a sweep item for the step, never fix it during the wait.
  - **An input the next step needs that the brief says is unknown** (a path,
    a drive, a name): end the reply by asking for it, one line, never guessed.
    Get the FULL list of inputs from the command itself: run `<cmd> --help`
    on the install the step will actually use. A brief that says "a folder
    the owner names" can omit a second required argument (a destination root), and
    the owner should answer both in one reply, not one per turn.
  - **A brief's claim about what a data artefact MEANS** ("these N journals
    are the answers for band X") is checked by joining it to its source,
    not by counting it. Bucket the items by their ORIGINAL verdict: a count
    that matches can still mix two populations, and the next step's
    measurement then rests on the wrong half.
  - **A brief that names ONE command as "the answer path" for a UI with
    several answer kinds.** List every answer the existing UI offers (accept /
    reject / correct / apply-to-all...) and map each to the
    command that performs it. Commands that deliberately store nothing or
    refuse a magic value usually cover only one kind; the uncovered kinds
    are a design decision (new CLI verbs vs. reusing the existing resolver)
    and belong at the top of the reply.
  - **A requested commit that cannot exist.** When the brief asks for "a
    separate commit" for a step, `git check-ignore -v` every file that step
    will touch. If they are all gitignored (a private harness, the wiki), git
    has nothing to stage. Say so in the shape and name the project's own rule
    for that case (e.g. end at the log entry). Never invent a public edit to
    make the commit exist. Also check that the brief names the right FILE for
    the gate ("the cases in check.py" when they live in the sabotage harness),
    and name which checker or test each case expects to go red.
  - **A brief that blames ONE layer** ("the CLI carries it, the window just
    drops it"). Trace the item end to end before writing a test: the
    producer's output dict (`json.dumps({...})`), the bridge/app layer that
    reshapes it, then the renderer. A field that is a COUNT (`already_filed:
    1`) is not the items; the renderer cannot draw what only a number
    describes. Also list EVERY branch that feeds the displayed number (the
    `continue`s in the planning loop: already there, duplicate, ambiguous)
    and check each one reaches the list; the same "count says N, list shows
    fewer" bug usually has siblings. Rebuilding the missing items in the UI by
    subtraction ("counted but not in moves") is wrong: it mislabels the
    siblings and is a side door around a CLI-first rule.
  - **A "dry run" that still writes somewhere.** Read the command's first
    lines: a plan-only mode that moves no files can still create dirs or
    add index/cache rows to the REAL database. Say so before it runs, so
    "dry run" is not taken to mean "touches nothing".
- any tooling friction encountered, and the method that worked instead

Then stop. Do not begin the next phase because the context is warm — the brief
asked for a wait, and a fresh agent starting work unasked is the failure the
wait exists to prevent.

**A GO brief with a conditional STOP** ("if you find X, stop and say so")
checks the condition FIRST, before the shape, the tests or any repo write: the
condition is a claim about the code, and a shape written before it is checked
may have to be thrown away. When it fires, stop the whole brief, including the
independent items ("one commit" ties them together), and reply with: where the
condition is true (file:line), the rejected shortcut and why, the compliant
fix with its size, which items are independent, and ONE decision question.

**When the brief names a known CATCH for the next step** (a rounding difference, a
size limit, a race), spend one throwaway scratch test on it before writing the
shape: it is a fact, so it is the coder's job, and its result often turns the catch
into the one decision the shape must put to the owner (with numbers). A scratch test is not
"starting the work"; touching the repo is.

**When the brief ends "then show the SHAPE for item X, no code", the pass
includes the code X touches.** Grep for an existing pattern that does the same
job elsewhere (a `--progress` stream on another command, a spinner the item
replaces). Read it, along with the Api method, the page handler and the markup
it drives. Then shape X as an extension of that pattern, quoting its real names.
A shape built without that reading invents a second mechanism.

## 5. The first move after the wait

When the owner then asks "what next?", the brief's NEXT line is the default answer,
not the only one — but a recommendation to deviate from it must be argued
against the decisions the brief records, not around them.

**Before recommending that a planned step be skipped, name the DECISION it
feeds and ask whether that decision is still live.** A step that gates an
option marked "rejected for now" is not dead work: "for now" means "until this
number exists", and the chosen shape may only look sufficient because the
option it competes with was never measured. Verdict form: "this step decides X
vs Y — do you still want Y on the table?", never "skip it, the current shape
does not need it". The second form silently recommends against the thing the owner
may actually want, and they have to catch it themselves.

When the owner checks their understanding of a component ("so the model decides?"),
answer with a who-does-what flow — one box per part, each labelled with its
single duty, and the point where the human stays in the loop. Translator vs
decider, script vs model, are the distinctions being tested; prose blurs them.

## Standing rules for this kind of pass

**Treat every claim in a brief as context to verify, never as fact.** The brief
is a previous session's belief. The repo is the truth.

**A warning that has fired many times and never once been real is tool
bookkeeping — but check it anyway, every time, with one cheap command.** The
cost of checking is one call; the cost of acting on a phantom is a session.

**A private, gitignored project memory is not recoverable from git.** Where a
project keeps its roadmap, wiki and agent rules outside version control, those
files are the only copy — read them, never rewrite them casually, and never
sweep them with a tool that honours `.gitignore`. Use
`rg -n --no-ignore --hidden -g '!.venv' -g '!.git' "<claim>" .` for that sweep.

**Approval-gated files are asked about LAST, once everything else is green.** A
prompt that times out early costs the whole session. If it does time out, stop
and say so — never route around it. The owner agreeing in chat is not the write
approval: the tool's own prompt is separate. When they say "re-run it, I'll
approve", re-issue the IDENTICAL edit once, then continue with the commit.

**A read-only AUDIT brief** ("hunt for rules decided differently in two
places, write findings to _private, do not fix") follows
`references/rule-drift-audit.md`: the doors-per-action comparison, the output
shape, and the drifts that recur.

**"Scratch empty at the end" means the Hermes scratch dir** (the path in the
runtime section), not `$TMPDIR`, which can resolve to the system temp shared
with every program. `ls -l` it with times. Anything older than the session
start is not yours: report its names, do not delete it.

## Pitfalls

**Citing line numbers from memory after a compaction.** Collapsed or demoted
outputs leave only your recollection. Re-`show` every cited range in one cell
before writing the deliverable.

**Re-reading to "be sure".** Certainty comes from the tracking list, not from a
second fetch. If you cannot say whether a file landed, the list was not kept.

**Summarising instead of reading.** A brief that says "do not paraphrase, read
them" means the reply must cite real sizes, real line counts, real quoted lines.
Claiming context you did not surface is the one unforgivable version of this
task.

**Answering the brief as if it were a work order.** A brief restated after a
context compaction is still the same single task. Re-running the whole reading
pass each time it reappears is how a session spends itself on orientation.
