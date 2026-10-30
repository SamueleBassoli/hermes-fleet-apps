---
name: project-memory
description: "Use when a project spans many sessions. Docs that stay true."
version: 1.1.0
author: coder role of hermes-fleet-apps
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [documentation, wiki, roadmap, handover, project-state, consistency]
---

# Project Memory

For projects that run across many sessions with the context deliberately reset each
time. The repo itself has to carry the memory: `handoff` moves one session to the next,
this skill keeps a project true to itself for months.

The failure this prevents: a fresh session opens a page, believes it, and builds on a
claim that stopped being true three sessions ago.

## The three-file split — one fact, one home

```
  _private/wiki/        what the project IS   shape, settled decisions, measured numbers
  _private/ROADMAP.md   what is LEFT         ordered phases, small steps, ticks
  _private/wiki/log.md  what HAPPENED        dated, append-only
```

The split is the whole point. Development steps in the wiki, or architecture in the
roadmap, means one fact lives in two files — and two copies drift.

**State the precedence, not only the split.** The log is dated history: its entries
describe what was true on their date, not what is true now, so where it disagrees with
the roadmap or a concept page, those win and the log stays as written. Put that beside
the read order in `AGENTS.md` — a fresh session sent to read the last 20 log entries will
otherwise treat the newest one it finds as current state.

**When content moves between these files, leave a pointer, never a copy.** "The plan
lives in ROADMAP.md, currently Phase 1" — not a restated step list.

Keep the roadmap out of the wiki proper: no wiki frontmatter, not in the wiki index, not
wikilinked. A wiki with a mechanical checker will otherwise flag it as an orphan page or
a frontmatter error.

Record the boundary in `AGENTS.md` as a rule, and put the read order there too —
otherwise the next session invents its own split.

## Session start

Read: current-state → roadmap → wiki index → last ~20 log entries. Batch independent reads
into one turn, but give each LONG document its own file-reading call — funnelling several
through a script's stdout head/tail-truncates the combined output, and the documents in the
middle are the ones that vanish. A re-read of a vanished path can then come back
deduplicated ("unchanged since last read", no content returned), because the earlier call
counts as having read it even though nothing reached context. When that happens, page the
spilled output file the tool names rather than re-requesting the path.

**In a batched script, index every tool result with `.get()` and never with `[...]`.** A
single `KeyError` on an unexpected result shape aborts the whole cell, discarding the
output of the calls that already succeeded and costing a full re-run — and result shapes
differ between a tool called directly and the same-named helper inside a code runner.
Print the raw dict once when a helper is new to you, then index it.

**Then verify before quoting any of it.** Run the test suite and the doc checker in the
same batch. A documented claim is a claim, not evidence; reporting a stale one as
current state is exactly what this layout exists to prevent.

**Re-derive state at the moment you REPORT it, not once at the start of the session.**
On a project where another agent, another terminal or the user may be committing, figures
gathered earlier in the same session are already a claim about the past — a repo can gain
two commits and forty tests between an opening read and the message that quotes it. Re-run
`git log -1 --format='%h %ci %s'`, the test suite and the checker immediately before
writing the report, and put the short sha in the report: a sha is the one figure a reader
can check against the repo, which makes a stale report detectable instead of merely wrong.

**Page a long document using a line count read in THIS pass.** Offsets computed from an
earlier read's `total_lines` land in the wrong section once the file has grown, and the
section they land in looks plausible — a roadmap that gained a phase silently shifts every
step after it. Re-read the length, or anchor on a heading string instead of a number.

Confirm repo state with commands too — `git status --porcelain`, `git log --oneline -5`,
`git ls-files | wc -l` — not from the docs. Then report in four buckets and stop: what
VERIFIED against the code, which claims are STALE with the correct value, what is MISSING
from the plan entirely, and anything left to DECIDE. Resist starting work inside the
orientation pass; the point of the pass is to find out whether the plan still applies.

### Reporting state to the user

The four buckets above are for deciding what to do next. When the USER asks where the
project stands, the shape is different and shorter:

```
  what it is        one line, plain words, no jargon
  verified now      HEAD sha, test count, checker count — each from a run in this message
  phases            the checklist, ticked, with the current phase marked
  where the gap is  the one thing half-built, write-only or unwired
  overdue           unblocked chores nobody has scheduled
```

Ticked checkboxes and short indented blocks, not paragraphs. Name the next step and stop
— offer it, do not start it.

**Audit the plan for OMISSIONS, not only for staleness.** Checking that every documented
claim is true is a completeness test of the docs, not of the plan — a roadmap can be
accurate on every line it contains and silent about the thing that will hurt most. The
verified/stale pass cannot surface a step that was never written, so ask separately what
is absent. Three categories recur and are worth checking by name in any long project:

- **No inverse operation.** Every create/write the tool performs, without the matching
  delete/undo/forget scheduled anywhere.
- **No idempotent re-run.** Running the main command twice over its own output is the
  normal daily use and is rarely anyone's step; verify it as one.
- **A blocking external constraint with no step behind it.** A licence, a quota, an API
  deprecation or a legal gate recorded in a decisions or rejected-ideas page is a note,
  not a plan. If it blocks a real objective, it is a step with a Verify line and an owner
  — a wall deserves a door, not a paragraph.

**Re-verify a recorded gap before scheduling work to close it.** "X has no test" in a dated
log entry is a claim about that date, and the usual way it stops being true is incidental: a
later step lifts a closure, extracts a seam or adds a fixture, and the previously unreachable
path picks up coverage nobody went back to tick. Grep the test tree for the SYMBOL — the
constant, the helper, the answer kind — before writing anything, then narrow the step to what
is genuinely still uncovered and say which part was already closed. Writing a test that
already exists is the cheap failure; reporting a gap to the user as open after it closed is
the expensive one.

**Verify what an unbuilt step claims to DELETE against the schema, not against its own
prose.** A roadmap entry naming the rows a command will remove is a claim about cascade
behaviour, and it is usually written optimistically. `ON DELETE CASCADE` on a join table
removes the ASSOCIATION, never the referenced row: deleting a subject drops the rows
linking it to its reference samples, while the sample rows — and the vectors, hashes or
blobs inside them — survive in the table that owns them, because those belong to the
asset, not to the subject. Run the delete on a throwaway database and print the row
counts before and after — tracing foreign keys by eye is how the optimistic wording got
there. An overstated deletion claim is the worst kind of stale doc to leave standing,
since the code can be entirely correct while the promise around it is not, and no test
fails.

**Give each question its own throwaway database.** Test runs that share one workspace let
an earlier mutating question supply the answer to a later one — run A creates the row and
run B "finds" it, reporting that the lookup works. A measurement produced by the
measurement before it is worse than none, because it reads as evidence. Build the state
from one named setup function called once per question, and print the state each run
actually saw. When two candidate calls are being compared, make the losing one demonstrate
its failure: "B resurrected a deleted row and reused its id" is what stops the rejected
option returning next session.

**When the claim is overstated there are two fixes, and the thorough-sounding one is
usually wrong.** Narrowing the doc looks like a retreat and widening the code looks like
integrity, so the second gets chosen on instinct. Measure what the widened code would
actually do before choosing: it frequently deletes a fraction while advertising the
whole, and it can corrupt the index it deletes from. `references/deletion-claims.md` has
the two tests to run and the mechanisms behind them — plus, further down, choosing the
public handle for a per-entry delete, keying a stored fact ABOUT a subject so the delete
reaches it, and the reverse cascade that destroys associations with no delete called at
all.

**A narrowed claim needs a clause in the step's Verify line.** Add "and the rows it does
NOT delete are still there" to the unbuilt step, or the correction is just a
differently-worded guess that nothing will ever catch.

**Verify the HELPER FUNCTIONS an unbuilt step names, not only its prose claims.** A step
written by an earlier session often prescribes the wiring — "resolve the names to ids via
`get_or_create_subject`" — and a named call reads as settled design rather than as a claim
nobody drove. Check each one's semantics against what the step actually needs. A
get-or-create in a position where the row must already exist is a create nobody asked
for, and it fires precisely when something else deleted that row mid-session:
it resurrects a subject with zero associations, the state the project's own delete
refuses to manufacture. A pure lookup plus an explicit skip is the correct shape there.
Say on the step which call it should use and why the prescribed one was wrong — the same
treatment an unbuildable Verify line gets, not a silent substitution.

**A recorded reason for DEFERRING a step is a claim, and it is the least-measured
sentence in the whole plan.** It is written at the moment appetite ran out, by whoever
wanted the work least, and it is then inherited as a settled decision by every session
after — "the honest default may stay X" reads as judgement, not as a hypothesis nobody
tested. Re-derive it before either building the step or dropping it. The usual outcome is
not that the risk was imaginary but that it was of a different KIND than the wording
claims, which changes what the step costs rather than whether it is safe. Record the
number on the step so the next session inherits a measurement instead of a mood, and say
plainly that the go/no-go has moved from "is this dangerous" to "is this worth the
effort" — the second is the user's call, and they cannot make it while the first is still
on the page.

Four moves turn such a sentence into a measurement, and each has its own failure:

- **Restate the objection as the failure it PREDICTS.** Deferral reasons are written in
  adjectives ("the input is mid-motion, so the result is unreliable") and adjectives
  cannot be measured. Force the observable: does the bad case produce a WRONG answer or
  merely no answer? Those have opposite costs — a wrong answer is damage, a missing
  answer is usually the system's own correct refusal — and the wording almost never says
  which it meant.
- **Measure the direction the feature actually runs.** Evidence that an input works well
  as a QUERY says nothing about it working as a REFERENCE; a benchmark proving a parser
  reads a format says nothing about it writing one. Name which direction the existing
  evidence covers before citing it as support for either side.
- **Walk the whole population, not the cases the system would pick.** Sampling the
  convenient ones and finding them fine may be luck. Enumerate every case, report the
  worst and the count that fail, and state the incumbent baseline the feature must beat —
  "good enough" is meaningless without that number, and the incumbent routinely scores
  worse than anyone assumed.
- **Check whether a bad input is INERT before designing a guard against it.** Read how
  the consumer aggregates: a max/best-of makes a weak entry unable to affect anything,
  while an average makes the same entry harmful. That one function read frequently
  collapses the objection entirely.

**Kill the plausible guard with the same pass, and report the negative number.** A
quality gate that sounds sensible — a sharpness threshold, a confidence floor — needs its
correlation against the outcome measured, not assumed. A metric already in the codebase
is often answering a DIFFERENT question (how confidently a thing was FOUND, not how well
it will PERFORM) and will reject better inputs than it passes. Write the correlation into
the step even though nothing was built from it, or the next session proposes the same
guard and re-derives the same refusal.

**A resurrected row often REUSES the id it had before deletion**, which is what raises
this from untidy to unfixable: the bad record is then byte-identical to a legitimate one
and nothing downstream can tell them apart. Drive it on a throwaway database — delete,
re-create, print both ids — before accepting any step that writes a stored fact keyed on a
subject.

**Test id reuse FIRST whenever one command hands out row ids that a later command acts
on** (a listing's `--json` ids fed to an `--apply`). SQLite `INTEGER PRIMARY KEY` without
`AUTOINCREMENT` gives the next insert max(id)+1, so deleting the newest rows frees their
numbers — and any "refresh" written as delete-then-reinsert (re-index, rebuild children)
can hand an old id to a DIFFERENT row while the caller's saved id still looks valid. Script
it with the project's own store functions on a throwaway db: two rows, refresh one
unchanged (id kept), refresh it to zero children and insert a new parent (id reused?).
If reused, stop before building and show the options with a recommendation: permanent ids
(`AUTOINCREMENT` via a versioned migration that preserves existing ids — fixes every
consumer), a per-id check value (id plus a content fingerprint, refused on mismatch), or
accept with a human-visible plan. A plan line saying "act on ids, never positions"
assumes ids are permanent; the test is what makes that true or false.

**A snapshot of NAMES taken before a long-lived process starts is stale by the time an
answer arrives.** A queue, worklist or rendered page built once at startup carries the
names that existed then; a delete from another terminal mid-session makes them refer to
nobody. Any write derived from that snapshot therefore looks up rather than creates, and
treats "not found" as a reason to skip the write while still honouring the user's
immediate action.

Say which gaps are real, which are narrower than claimed, and prove the difference by
running something rather than by reasoning about it.

**A finished-but-uncommitted step must be committed before the next one starts** — a
next step that fails halfway otherwise sits in the same diff as completed work, with
nothing clean to roll back to. **But OFFER the commit and wait; never commit, revert,
stash or tidy a dirty tree on your own initiative.** A working tree left dirty between
sessions is a normal handover state, not mess: the user may be holding the diff for
review, for a different commit message, or to demonstrate the change. Cleaning it
destroys the one artefact the session was handed.

When a brief states which files are dirty and why, diff that list against
`git status --porcelain` before touching anything. A mismatch means the brief is stale
or another process wrote to the tree — report it instead of reconciling it.

**Disprove a phantom "file modified by another agent" warning with the same four outputs
every time, including after it has been benign a dozen times.** `git status --porcelain`
(does it name any other writer), `git diff --numstat` (is the change only the lines this
session just wrote), the file mtimes (seconds old, or older than the session), and
`git stash list` (empty). Tool bookkeeping and a genuine concurrent writer produce identical
warning text, and they are separable only in those four outputs — skipping the check because
the last ten were harmless is how the eleventh gets committed.

**A gap or bug NAMED in a brief must carry the command that checks it.** When writing the
handover, an unqualified "X has no test" or "Y is broken" sends the next session either to
duplicate work already done or to spend its first hour re-deriving what one grep settles.
State the check beside the claim; the reader is going to verify it regardless, so decide
whether that costs them one command or an hour.

## Roadmap format

Phases in build order, each broken into numbered steps small enough for one sitting.
Every step carries a **Verify** line naming something to run:

```
- [ ] **1.2 Image endpoint.** Serve a downscaled JPEG with boxes drawn, generated
      in memory, never written.
      *Verify:* request the endpoint, get a valid JPEG; nothing new on disk.
```

- **A step with no Verify line is a wish, not a step.** Without one the box gets ticked
  on optimism and the roadmap stops describing reality.
- Tick only after the Verify line actually passed — never on "that should work now".
- **When a step is WIRING, build the test seam before the wiring.** A call buried in a
  closure inside a server loop, request handler or callback is reachable only by driving
  the whole stack, so the test that would prove the connection does not exist — and a test
  calling the new helper directly proves the helper and nothing about the wiring, which is
  the entire content of the step. Lift the closure into a named factory that returns it,
  test through that, and leave any injected-callable boundary intact so the architecture
  rule it enforces still holds. A long-lived nested closure is usually also why a
  neighbouring feature has no unit test at all; say so on the step when you find it, since
  that gap is now cheap to close and nobody scheduled it.
- **Check the Verify line is demonstrable before implementing the step**, not after.
  A plausible-sounding verification can be impossible by construction — "refused
  from another host" cannot be shown for a service bound to loopback, because the
  other host never reaches the socket. Restate it as what the step actually buys,
  and say so on the step, or the work gets ticked against a test nobody ran.
- **Never delete a dropped step.** Mark it `[-]` with the reason on the same line;
  deleted rationale comes back as a fresh idea two sessions later.
- Work found mid-phase is inserted as a numbered step, not held in the head.
  **A side bug noticed while building something else (a test that exposed old rust, a
  pre-existing sabotage miss) goes into the project's dated fixes file or parking lot
  in the SAME step it is seen**: what happens, the command or test that shows it, what
  should happen instead. Mentioning it only in a chat report is not recording it:
  context compaction keeps the task and drops the aside, so a later "write up those two
  bugs" finds nothing in the repo, nothing in the summary, and no way to answer except
  guessing. When asked to write up a finding that was never recorded, say plainly that
  it cannot be reconstructed, list the nearby recorded items it could be confused with,
  and offer two paths: the user supplies the original wording, or the bug is re-found by
  experiment on fake data and labelled as newly found.
- Legend at the top: `[ ]` todo · `[~]` in progress · `[x]` done · `[-]` dropped.
- **Name phases, never number them.** Order is the file's order; an ordinal in a label
  is a claim about every OTHER phase, so inserting one in the middle invalidates every
  document that referenced a later phase by number and forces a repo-wide sweep. Named
  phases (`review · forget · rules · assign · video`) ripple nowhere on insert, and no
  dated log entry is left describing a number that has since moved. Steps become
  `<phase>.<n>` — `forget.1`, `rules.2`.
- **Keep already-shipped step ids frozen when adopting the naming convention.** Ids
  cited in test docstrings, module comments or a doc checker are shipped identifiers;
  rewriting them to relabel finished work is the exact churn the convention exists to
  avoid. Rename unbuilt phases, freeze the built ones, and say in the roadmap which is
  which so the split does not read as an oversight.
- Before relabelling anything, grep the repo for the labels first: if no detector or test
  asserts on them, the rename cannot break the build, and knowing that costs one command.
- A risky phase opens with a spike step whose Verify produces a number, and says the
  phase may be killed there. Cheaper than finding out at step 4.
- **A phase-closing step is a COVERAGE audit, not a consistency one, and both gates being
  green is what makes it dangerous.** The checker reads links, frontmatter and claims, so it
  cannot see a page that should mention the feature and never does, and the suite cannot see
  a function nothing calls. "Tests, wiki and README updated" is otherwise ticked on the
  assumption that earlier steps covered it. Run the audit before fixing anything, and expect
  it to find work in categories the gates are structurally blind to. Procedure, the three
  detectors and the deletion rule: `references/phase-closing-audit.md`.
- **A gap enters the plan when the PRODUCT was seen to mishandle something — never
  because a throwaway test hit an error while measuring something else.** A spike or
  sabotage harness walks files and calls libraries directly, outside the code path the
  tool actually uses, so its stack traces are evidence about the test. The shape is
  seductive because the error is real, the output is in front of you, and writing it up
  feels like diligence: a decoder failing on a file the test opened becomes "the tool
  misreports undecodable inputs", a step with a Verify line nobody can run. Before
  writing the step, name the command a user would type and the observation it produced.
  If you cannot, it is not a step. The same test disqualifies a symptom found in a file
  that was never part of the project — a stray in the user's own folders is not a
  corpus, and the user will say so.
- **Park the thought with the reason it is NOT scheduled, rather than deleting it.** The
  observation may still be true; what it lacks is evidence that the product is affected.
  A parking-lot entry saying what was seen, through what, and what would have to happen
  for it to become a step keeps the next session from rediscovering it and scheduling it
  properly this time.
- **A step that changes a SHIPPED schema carries a migration, and the version stamp is
  the only thing that makes its absence loud.** `CREATE TABLE IF NOT EXISTS` creates a
  missing table but is a silent no-op on one that exists in the wrong shape, so a startup
  script that runs the current schema text migrates new TABLES into existence while doing
  nothing about a changed COLUMN — the mismatch surfaces a release later as `no such
  column`. Any step adding a column, relaxing a constraint or widening a table therefore
  owes a migration, a version bump, and a Verify line that opens a database built from
  the OLD schema text. Procedure, the rebuild that preserves public ids, and the SQLite
  NULL-uniqueness trap: `references/schema-migration.md`.
- **Shape-only phases ("add to the plan, no code") start from the facts the phase
  depends on, read from the code first** (where the version lives and whether it is
  written twice, what is fetched at runtime vs shipped, where user data lives, the
  licence of each shipped asset). Put them in a "facts checked" block above the
  phases; give each phase a shape, open questions each with a proposal, and a Verify
  line. Leave version-dependent tool choices open ("check current docs before
  choosing"), propose an order by dependency marked "owner to confirm", and default any
  network contact to off or button-only with what the remote side sees stated.
- Parking lot at the bottom: unscheduled, not forgotten, not scheduled either.

The upkeep must be one character (`[ ]` → `[x]`). Anything heavier gets skipped, and a
roadmap nobody ticks is worse than none.

## Closing a change

Done means code, wiki and README agree — not that the code runs.

1. Supersede the wiki page that is now wrong. Keep the wrong reasoning visible with the
   correction, so it is not re-proposed as a new idea.
2. Tick the roadmap step.
3. One dated log entry: decision / create / fix / cleanup, plus the reason.
4. Run the doc checker and the test suite.
5. Sweep for the old claim across wiki, AGENTS.md, README, comments and docstrings. A
   correction landing in one file and not the others *is* the contradiction.

```
rg -n --no-ignore --hidden -g '!.venv' -g '!.git' "<old number or claim>" .
```

**Prove the private side is still ignored immediately before staging**, not from memory:
`git add -A --dry-run` to see exactly what would be committed, and `git check-ignore -v`
on the private paths to see the rule that covers each. Both are read-only and cost one
command. A private file reaching a commit cannot be fixed by a later `.gitignore` edit.
The dry run stages NOTHING: follow it with `git add <explicit paths>`, then check
`git log -1` and an empty `git status --porcelain`. A commit chained after the dry run
reports "nothing to commit" and is easy to miss.

**Compare that dry-run list with the list of TRACKED files this session edited, one by
one.** A tracked file missing from the list means the edit never landed on disk. A patch
result can look like success in the transcript (a deduplicated or elided tool output)
while the file is unchanged. Grep the file for the new sentence, re-apply the edit, and
re-run the gates before committing. Otherwise the commit ships the code without its
docs, and every gate stays green because nothing checks that prose exists.

**Write the commit message as the reasoning, not as a label.** In a project whose memory
is gitignored, the commit log is the only durable record a future reader can reach — so
the body carries what the code cannot show: the bug's mechanism, what was rejected and
why, and the constraint that made the chosen shape necessary. A one-line subject with no
body is a fact already visible in the diff. Subject in the imperative naming the
behaviour change; body in prose paragraphs.

**The sweep must include hidden and gitignored files, and a default content search does
not.** Ignore-aware search tools skip exactly the private side of the repo — the wiki,
the roadmap and the agent instruction file are ignored by definition — so the prescribed
sweep returns zero matches while reporting success, mentioning the skipped files only in
a warning that is easy to read past. Measured on a real project: a default sweep for a
stale phase label found 0 hits with the string sitting in three files, and every
"consistency sweep" that project had ever run had searched only its public tracked files.
Write the ignore-defeating flags into the instruction file, and run the documented command
verbatim once to confirm it reaches the private side.

The dated log is append-only and exempt. An old number inside a log entry is what was true
on that date, not a contradiction; correcting it destroys the history the log exists for.

This fires for more than features: a better method found, a change of mind on something
already built, a number re-measured, a conclusion proven wrong.

**When the plan's own wording turns out to be unbuildable, correct the plan and record
why — do not quietly build something else under the old label.** Tick the step, then
state on the same step what was actually built, what the original wording would have
done, and which alternative was rejected. A step ticked as written while the code does
something different is the exact drift this layout exists to catch.

**Reorder steps out loud when the listed order ships something that cannot be
acceptance-tested.** A step that EXPOSES an identifier must precede the step that
CONSUMES it: with no listing command, the consumer can only be tested against a
hand-seeded value, which proves the query works and proves nothing about the command
being reachable by the person it is for. Build the read surface first, then tick it in
place with a note saying the file's order was reversed and why. The step order is a plan,
not a promise — but a silent reorder leaves the next session unable to tell a decision
from a mistake.

**A phase heading that describes a gap must be rewritten the moment the gap closes.** A
preamble reading "the delete that does not exist" survives the step that built it,
because ticking a checkbox does not touch the prose above it — and a fresh session reads
the phase introduction before the step list. Put the phase's own framing in the sweep,
and restate it in the past tense with one line on what the phase has left to do.

**Sweep your OWN earlier writes in this session, not only what previous sessions left.**
A decision transcribed into the instruction file at the start of a session is as
superseded as a three-month-old page once the same session's later step reverses it, and
it is the copy least likely to be swept — recent memory of writing it reads as knowing it
is current. This fires whenever a session both records a limitation and then removes it.
The correction is a rewrite in place stating what was true before, what changed it, and
which part survives; an append-only dated log is the only file exempt, and there the
correction is a new entry.

**When a refusal becomes a capability, the REASON STRING it printed is now dead code.**
A user-facing constant explaining why something is withheld outlives the branch that
returned it, still imported by every module that once needed to say it, because deleting
a guard leaves the import untouched and nothing fails. A dead constant whose comment
states a limitation the tool no longer has is worse than an unused symbol: the next
session greps it, finds the explanation, and treats it as current design. Grep the
constant's name after removing the branch — if no caller remains, delete the constant,
its comment and its imports in the same commit, and rewrite any test asserting its
ABSENCE to assert the new control's own markup instead. A test written as "the excuse is
gone" passes when the feature is silently dropped altogether.

**Sweep the shipped step's own ID, not only the claim whose wording changed.** A source
comment or a user-facing string that defers behaviour to a future step — "acting on this is
step X", "remove one with <command>, which arrives in X" — is true when written and false the
moment X lands, and no claim-based sweep finds it, because the sentence never described the
present. Grep the id of the step just shipped, and the id before it, across source,
docstrings and printed strings; a deferral comment left standing also keeps the user-facing
line it justifies deliberately weaker than what the tool now does. The inverse costs more and
is found only by RUNNING the tool: a string shipped earlier that advertises a command or a
behaviour the code does not have yet reads to the user as an instruction. When a step closes
a hole, check whether the tool has already been telling somebody the hole is closed — and
when a step OPENS a capability, check whether the tool is still telling somebody it is
missing. Both directions, every time.

**A user-facing string that makes a promise needs a test that owns it, or the wording rots
with every gate green.** A test asserting the output mentions the subject and the outcome
passes unchanged when the sentence around them still defers the behaviour to a future step,
so the weakened wording survives every later phase: nothing failed, nothing contradicted a
doc, and the checker reads links rather than tense. Assert the distinctive clause of the
promise itself, not only the values interpolated into it.

**Sweep for the stale claim by SEARCHING, not by remembering which files to open.** A
feature's status is asserted in more places than the page that owns it — a README
capability table, a command reference row, a module docstring, an architecture note. Grep
the old claim's distinctive phrasing across the repo and fix every hit in one pass.

**When inserting a bullet ABOVE an existing one, the patch anchor is the whole existing
bullet, re-emitted after the new text.** Anchoring on the neighbour's first line alone
replaces that line, and the survivor's continuation lines are silently orphaned under
the new bullet — a page that still reads fluently and now states something nobody
decided.

**Re-run the sweep AFTER patching, not only before.** One file usually states the claim
twice — once in a summary structure (a table row, a bullet, a heading) and once in the
prose that introduces it — and a patch aimed at the structured copy leaves the paragraph
above it intact. The second sweep is what catches that, and it costs one command.

**Check whether a doc statement describes the feature you changed or a neighbouring one
before rewriting it.** Rows that look stale often describe a different command that still
behaves that way; rewriting them introduces a fresh contradiction while closing an old
one.

**Verify every claim against the code before promoting it from the log into the
instruction file.** A dated entry or a handover brief compresses a mechanism into one
sentence, and that is fine where it sits: the log is dated and append-only, so a loose
paraphrase stays as written. The instruction file is read as present truth by every later
session, so the same sentence becomes permanent there and gets defended. Open the
function before transcribing. Two shapes recur — a verb that overstates the algorithm (a
RANKING described as a filter, which implies an empty result the code cannot return and
deletes the reason the ranking exists), and a helper named one level off (the shared core
instead of the wrapper the caller actually reaches, so a future grep for the named
symbol lands in the wrong module). Correcting the brief is part of the transcription, and
the correction is worth saying out loud: the user is deciding how much of the rest of
that brief to trust.

**Protected instruction files may refuse the write.** When the rule you added belongs in
a file you cannot edit, record in the dated log exactly which rule is owed and to which
section, and tell the user it is outstanding. An undocumented gap between the code and
its instruction file is what the next session trusts first.

**A gitignored instruction file cannot ride a commit.** When asked to put an
AGENTS.md edit "in the same commit", check `git check-ignore -q AGENTS.md`. If it is
ignored, say so in one line and apply the edit anyway. Then copy it to the backup and
record it in the dated log, because the log and the backup are the only durable
record it has. Never force-add it to make the request literally true.

**The user's "yes" in a question is not the write approval.** A protected file has its
own approval prompt at the moment of the write, separate from any clarify answer that
preceded it. If that prompt times out, stop, show the exact edit, and ask them to reply
when they are at the keyboard to approve it. Re-issue the identical edit only after
they say so. Never re-issue it through another tool.

## Enforce mechanically or not at all

**A rule with no detector is a good intention.** A doc-consistency script beats a
paragraph asking future agents to be careful: constants in code vs constants in every
doc, architecture rules still true in the source, forbidden imports, broken links,
missing frontmatter, orphan pages, personal data in public files. Exit 0 or fix it
before stopping.

**Assert a `.gitignore` rule by asking git, never by searching the file's text.** A
commented-out rule still CONTAINS its own pattern, so `"_private/" in gitignore` stays
True with the private side fully exposed. Run `git check-ignore -q <path>` per private
path and require exit 0 — and check the inverse too, that a public source file is NOT
ignored, or a broken rule silently stops shipping the product.

Verify the checker by deliberately breaking each thing it claims to catch and restoring
it. An unexercised checker is an untested test.

**A check that passes for the wrong reason is worse than no check.** When a test is a
text search, confirm it fails when the thing it guards is removed — a loose pattern
matches an identical line elsewhere in the file and stays green with the real guard
deleted. Anchor it to wording unique to the code path under test, then re-break it to
confirm it now fails for the right reason.

**Give each layer of a defence its own claim.** When a rule is enforced in two places —
the planner that must not propose the operation and the executor that must not perform
it — one detector covering "the rule exists" passes while either half is deleted, because
the other half still matches. Write one claim per enforcement site, and verify each by
deleting only that site.

**But duplicate a guard only where the duplicate is reachable INDEPENDENTLY.** Defence in
depth is for an executor many callers reach, where a caller that forgot to check must
still be safe — there, both sites are load-bearing and both get tested. A helper with
exactly ONE caller is the opposite case: a second copy of the rule inside it buys no
safety and costs proof, because a single test then passes with either copy deleted, which
is precisely what makes a headline test useless as evidence. Put the policy in the caller
beside the plan the user reads, let the helper perform the operation and decide nothing,
and say in the docstring which shape was chosen and why — the next session will otherwise
"harden" it by adding the redundant check back.

Count the callers before choosing. One caller → one guard, one test, proved. Many callers
→ one guard per site, one test per site.

**You usually DISCOVER a shadowed layer when its sabotage comes back inert, and the
question then is "is this layer reachable", not "is this test redundant".** A guard can be
correct and its test honest while a later check in the same path refuses the input anyway,
so removing the first changes no outcome. Settle it by driving the state that would reach
the layer rather than by reasoning about it: if some input reaches it, the FIXTURE was
wrong and must be pushed into that state; if nothing can, the layer buys no safety and
goes. The usual cause is a sentinel sharing a namespace with user data — a reserved folder
or bucket name travelling through the same field as a real subject name — because the
lookup resolving it fails first and masks the dedicated gate.

**Break each guard SEPARATELY and name the test or check that must fail.** "A test
failed" is not verification; *which* test failed is. A guard removed in isolation must
fail the test written about that guard — if a different one fails, the coverage is not
where it is believed to be. Also force the guard vacuously TRUE, not only absent:
deletion proves the suite notices a missing check, always-firing proves it notices a
check that silently disables the feature it protects.

**Prove the SABOTAGE changed behaviour before concluding a test is redundant.** An
injected break can be inert — neutralised by the statements around it — and then the
suite stays green for a reason that has nothing to do with coverage. The classic
mechanism is ordering: a destructive statement placed after the statement that supplies
its input reads rows already deleted, matches nothing, and runs as a no-op. Green here
looks like proof the test is unnecessary; it is proof the sabotage was. Before trusting
a passing result, confirm the broken build actually behaves differently — print the
rows, diff the output, or re-order the injection so its inputs still exist — and only
then judge the test.

**The second mechanism that makes a sabotage inert lives in the FIXTURE, not in the
code.** Swapping one identifier for another changes no output when the fixture makes the
two coincide: a fixture that joins every row it creates runs both id counters 1, 2, 3 in
step, so printing the wrong id prints identical numbers and the whole file stays green.
When an injected break changes nothing, suspect the fixture before concluding the test is
redundant. Fix it by forcing the values apart in setup — create one row that is
deliberately never joined, so the counters diverge — and ASSERT inside the fixture that
they differ, making the divergence its stated contract rather than an accident of
insertion order. Any test distinguishing two id spaces is worthless without it.

**A fixture also leaks a value through a CHANNEL the assertion did not mean to read.**
An assertion that the output NAMES something passes on any path, filename, id or label
that happens to contain the same string — file a subject's assets under a folder named
after the subject and "the plan names the subject" is true from the path alone, so the
sabotage that deletes the naming changes nothing. Keep the asserted value out of every
other field the command prints (use neutral fixture paths), ASSERT in the fixture that it
appears nowhere else, and anchor the assertion to the specific line that makes the claim
rather than to the whole captured output.

**A sabotage that does not COMPILE reads as a sabotage that changed nothing.** A broken
edit makes the suite error out before any test runs, and a harness scraping only lines
that say FAILED reports an empty list — identical to the output of a redundant test.
Count errors, collection failures and any non-standard exit code as failures, and treat
"pytest exited without naming a test" as a harness result in its own right.

**Run a sabotage pass from a SCRIPT with a `finally` that restores every file, never from
a long-lived interpreter session.** A kernel killed by a timeout mid-iteration leaves the
injected break sitting in the source, which then looks like an unexplained modification
or, worse, gets committed. Hold the originals in memory, restore in `finally`, and check
`git status --porcelain` afterwards regardless of how the run ended.

Full taxonomy of inert sabotages and the pass procedure: `references/sabotage-verification.md`.
A harness to copy and edit: `templates/sabotage_pass.py`.

**A rule written for one file must be checked on every file that can breach it.** An
import ban enforced only on the module that must not import the writer misses the module
*it* imports — the breach lands one level down and the check sees nothing. Enumerate the
chain the rule actually protects.

**A checker cannot check claims about itself.** "87 checks" written into the wiki drifts
silently the moment a check is added, because the count is the one number outside its own
coverage. Same for test counts, module counts, public-file counts. Either let the tool
print its own number and document none, or add a self-check that reads the tool's output
and compares it to the docs.

**Explain an unexpected change in a checker's total before accepting it.** Checks written
as per-file loops multiply: adding one test file can raise the count by the number of
markers that loop over the test tree, with no new check authored. An unexplained increase
is indistinguishable from a test that started passing for the wrong reason, and a
number accepted without a cause is copied into the docs as fact.

When a number describing the project's own tooling appears in a doc, treat it as
unverified until the tool has been run this session and the two agree.

**A note telling future readers to re-derive a number is not a detector.** A line
reading "count this with git, not from memory" sits beside a figure that goes on
rotting — the warning is read after the figure has already been believed. Either
the checker derives the number or the line states no number at all; a caveat is a
third option that fails every time.

**Update such a number by RUNNING the command and reading its output — never by adding
your delta to the figure already written.** Arithmetic on a stale base inherits the
staleness and produces a fresh wrong number that looks freshly checked, and it happens
even to a reader who just read the warning, because adjusting a number feels like
verifying it. Watch the off-by-one in composite forms: "release plus N commits" requires
deciding whether the release commit is inside N, which is exactly the ambiguity that made
the line wrong the first time.

**Never write a count that only becomes true after the pending commit.** Doc
numbers describing repo shape — tracked files, commits since the release, test
count — get written while finishing a step, and are wrong until it lands. A
session that stops before committing therefore leaves a doc describing a repo
that does not exist, and the next session inherits an off-by-one it has to
discover. Re-derive them from `git ls-files`, `git log --oneline` and the test
run at closing time, after the commit, not while writing the work up.

Prefer a form that cannot drift: branch plus HEAD short sha beats "0.1.0 plus
four commits", which is also ambiguous about whether the release is one of the
four.

**Count the copies of a repo-shape figure before scripting its replacement.** A version
line typically lives twice in one page — the header summary and a "Repository" list at
the bottom — with slightly different surrounding words, so a single-string replace moves
one and leaves the other stale. `rg -n 'plus .* commits'` first, then one replacement per
hit, each asserted to match exactly once BEFORE any write lands.

**Detect a file's line endings from BYTES, never from `read_text`.** Universal-newline
translation turns every CRLF into `\n` on read, so `"\r\n" in text` is always False and a
CRLF file gets rewritten as LF without any error. Check with `file <path>` or
`b"\r\n" in path.read_bytes()`, per file — a project's docs are not uniform, and a brief
saying "the wiki is CRLF" is a claim about whichever file its author last touched. A
single long-lived doc is often MIXED (count `b"\r\n"` against `b"\n"`), so any
read-then-rewrite normalises every old line, even one that "keeps the file's ending".
Append to a log or review doc in binary append mode (`open(p, "ab")`) with the ending most
of its lines use, and verify `new_bytes.startswith(old_bytes)`; if a rewrite already
happened, restore the old bytes from the backup copy (after checking its decoded text
equals what was read) and re-append.
The same trap fires on WRITE for source files: `write_text()` on Windows emits CRLF, so a
scripted replace turns an LF source file into a whole-file line-ending change and breaks
every later exact-match edit. Edit with `read_bytes()`/`write_bytes()` and confirm with
`git ls-files --eol <file>` (`w/lf` when `.gitattributes` says `eol=lf`) before the diff
is reported. A NEW file is untracked, so `git ls-files --eol` prints nothing for it, and
the file-writing tool can save it with CRLF: check every new file with `file <path>` and
convert to the project's ending before the full gate.

**Name the user's real data stores in the instruction file, with their before/after
check.** A brief that says "real db unchanged" without saying WHICH file lets a session
check a dev database for weeks while the real one goes unwatched. Give AGENTS.md a
section listing each real store (path, size, date, what it holds) and each look-alike
that is NOT real; check both before and after every job; when the reference size or date
changes for a legitimate reason (the user used the app), record the new reference in the
log. Read SQLite's traces before calling a change foreign: the main file growing while
the `-wal` vanishes is a checkpoint, i.e. the user's app closed; a fresh EMPTY `-wal` and
`-shm` with the main file unchanged is a read-only open (another agent counting rows).
List the processes holding it, report the reading, and let the user confirm the new
reference. When the user corrects which store is real, fix every non-log mention in one sweep
and say plainly which earlier reports checked the wrong file.

## Parallel streams in git worktrees

When two workstreams run at once (a fix on main, plus a spike, plus a measurement by
another agent), give each one a worktree and a branch cut from the same commit:
`git worktree add ../<Repo>-<stream> -b <stream> <sha>`.

**The main folder is the project's home; every worktree is temporary.** The owner
develops, runs and installs from main. A worktree lives only until its branch merges into main,
then the folder and branch are removed. So: frame main as the destination, never as a
peer stream ("merge main into ui" is only a catch-up; the goal is ui INTO main); the
log entry and any install happen in main; and never merge into main while another
agent is working in the main folder.

**When the owner asks "which worktree are we on?", answer from a fresh inventory, as a map.**
`git worktree list`, then per folder: branch, `git log -1 --format='%h %ci %s'`,
`git status --short | wc -l`, and `git merge-base --is-ancestor <b> main` (plus
`git rev-list --count main..<b>` when not). Report one line per folder with owner
(me / other agent / done), mark which branches are fully in main (their folders are
leftovers to remove once no agent uses them), and name this session's single folder.

**Two agents on one project: approval prompts time out unseen.** A prompt appears only
in the terminal of the agent that raised it, so while the owner reads the other session it
expires. Tell them to stay in that window for steps that need approval, and split shared
resources explicitly when handing a note to the other agent: who writes the log first,
which scratch files each may delete, who refreshes the backup last.

- **The memory layer is NOT in a new worktree.** Gitignored AGENTS.md, `_private/` and
  `.venv` exist only in the main folder. Every brief must point there.
- **Test the worktree's own source with the main venv:**
  `PYTHONPATH=src ../<Repo>/.venv/Scripts/python -B -m pytest -q -p no:cacheprovider`.
  The editable install otherwise imports MAIN's code, and a green run proves nothing.
  Print `pkg.__file__` once to confirm.
- **Gate scripts that find the repo from their own path check MAIN, not the
  worktree.** Say so in the brief.
- **Split streams by file** and name the off-limits files in each brief. Two streams in
  one module collide at merge time.
- **A stream on real data works on a COPY** (a SQLite file together with its
  `-wal`/`-shm`), never the live folder. A measuring stream delivers a table for the
  user to choose from: no constant changed, no commit, until they pick.
- Fast-forward a spike worktree (`git -C ../<Repo>-ui merge --ff-only <sha>`) onto new
  main commits it should build on. Record every worktree and its owner in the roadmap.
- **A gate that turns red in a worktree without an edit usually moved with main.** The
  checker lives in main's gitignored `_private/`, so another stream's commit to main
  (a re-measured constant plus its updated check) fails every unmerged worktree at once.
  Prove it is not yours with `git stash`, re-run, `git stash pop`; then catch up with
  `git merge main` and re-run both gates, rather than editing the check or the constant.

## Private material in a public repo

**Gitignoring the memory layer also excludes it from every git-based backup — so it has
no backup at all unless you give it one deliberately.** The three private files are
ignored by design, which means they are not in any clone, not on any remote, and not in
a `.git` tarball: a "back up the repo before moving it" step that archives `.git` restores
the code perfectly and loses the entire project memory, silently, because the restored
tree looks complete and the tests pass. The mechanical checker usually lives in the
private tree too, so the same event also deletes a gate — and unlike the docs it is real
code that has to be rewritten from the source it checks. Give the private tree its own
copy on separate storage, refresh it whenever the wiki changes, and verify the copy by
listing the checker and the log inside it rather than trusting that the copy ran.

**When that copy is a CLONE, its two halves need two different syncs.** A repo whose
memory layer is gitignored has a tracked half only `git` can move and an ignored half
only a file copy can move; refreshing one and calling the backup current is the failure
shape. Fetch the tracked half into the backup
(`git -C <backup> fetch <live> <branch> && git -C <backup> merge --ff-only FETCH_HEAD`)
for the branch checked out there. `git push <backup> main` from the live repo is
refused the same way: a non-bare clone will not take a push to its checked-out
branch. When the user says "push to the backup", run the fetch + ff-merge from the
backup side, which gives the same result, and say that you did. Never use the
backup's `origin` (usually GitHub). `fetch <live> main:main` is refused for a
checked-out branch, so a combined `fetch <live> main:main ui:ui` moves nothing. Update
every other branch with its own `fetch <live> <b>:<b>`, then confirm with
`git -C <backup> branch -v` that each branch sits at the live sha. Do not copy files over
a clone's working tree — a copy leaves that clone's own
HEAD and index describing an older commit while its files claim otherwise, so the backup
reports itself healthy at the wrong revision. Copy the ignored half separately.

**Verify such a backup by HEAD sha plus a clean `git status` inside it, not by `diff -rq`
alone.** Git normalises line endings on commit, so a correctly synced tree lists every
CRLF source file as differing and the verification reads as a failed sync. Confirm each
reported difference with `diff --strip-trailing-cr` before acting on it; identical shas
and an empty status are the evidence, and the diff is the noise. Exclude generated
folders from that diff (`-x .git -x .venv -x __pycache__ -x .pytest_cache -x
'*.egg-info'`). They are rebuilt on demand and never belong in the backup, so a diff that
lists them is noise too.

**Refresh the ignored half whenever it changes, not only on commit.** A step that edits
only private files (a spike, a roadmap tick, a log entry) makes no commit, so "refresh
after every commit" skips it. Copy the private tree at the end of every step that
touched it, and say so in the report.

**Copy to the backup only AFTER the write is proven, never in the same parallel batch.**
A write cell that dies (a reset code kernel losing its variables) leaves the file
unchanged, and a copy running beside it then "syncs" the old bytes; `cmp` passes because
both sides are equally stale. Sequence it: write, assert the new marker is in the file
(`b"Step 7 shape" in p.read_bytes()`, count == 1), then copy and check the marker in the
backup copy too.

**`cp -r` of the ignored half only adds and overwrites; it never deletes.** A private file
removed in the live repo (old spike scripts, retired shots) survives in the backup, and
`diff -rq` then reports it as "Only in backup". Remove the same paths in the backup in the
same command, then diff.

**Before deleting helper scripts "if nothing else uses them", grep the WHOLE tree for
their file names, ignored side included** (`grep -rn "step5_\|step6_" . ` minus `.git` and
`.venv`). Hits in notes are not uses, but each note that says "scripts kept: X" becomes
false: append one line saying they were deleted after commit <sha>. Hits in tests, checks or
other scripts mean stop and say so.

**Write the backup's PATH where every session reads it, not only in a handoff.** A brief
that says "backup identical" without the path leaves the next session unable to refresh
it, and searching the user's drives to find it is not allowed. Record the location and
the refresh rule in persistent memory (it spans projects) the first time it is learned.

**A dated append-only log is the one file no reconstruction can replace.** Code comes
back from the remote, the roadmap's remaining work is re-derivable from the code, and
measured constants usually survive inside the instruction file — but recorded reasoning
about decisions nobody remembers making cannot be regenerated, and inventing plausible
entries to fill the gap destroys the log's only property. When it is lost, say so and
start a fresh log at the current date.

### Rebuilding the memory layer after it is lost

Both gates stay green over an empty `_private/`, which is why the loss goes unnoticed for
a session. Rebuild in this order, and only from what can be verified today:

1. `current-state` from the parser, schema, config and matcher — read the code, not the
   brief that described it.
2. `ROADMAP.md` from open work. **Every reconstructed gap must cite the code location it
   derives from (file + approximate line).** If no line can be named, the gap was invented
   from the brief's wording, not found — grep the symbols the gap names before writing it.
3. `EVALUATION.md` from constants that survived in the instruction file; state which
   figures are lost rather than filling them.
4. Schema, index, a NEW log with one entry saying what was lost. Reasoning pages
   (rejected decisions, spike history) are not reconstructed; a page saying "unknown —
   lost" beats a plausible one.
5. **Add a checker group that fails when the memory layer is missing**: each
   start-of-session file exists and contains a marker unique to it (the roadmap's legend,
   the constant the evaluation justifies), every wikilink resolves, concept pages carry a
   status, the roadmap has no frontmatter and no numbered phase, the log has no entry dated
   before the loss (guards against invented history), and `git check-ignore` covers the
   private paths. Prove the "file missing" case with a rename from a throwaway
   finally-restore script — a text-replace sabotage harness cannot express it, so its
   permanent cases exercise the marker check instead.

**Write link-syntax examples in a schema page as prose, not as a literal link.** A
wikilink checker reads the example as a link and reports the schema page itself as the
first dead link.

- After creating any private file, prove it is ignored instead of reading `.gitignore`
  and assuming: `git check-ignore -v <path>` must name the rule that covers it.
- `.gitignore` does not untrack what is already committed. If private material reached a
  commit and nothing was pushed, remake the commit clean.
- **Never paste output from a run over real data into a public doc — and never compose
  output from memory either.** Run the command in a throwaway directory seeded with the
  docs' own placeholder names, then paste that verbatim: the neutral names keep personal
  data out, and the real run keeps the lines a composed sample forgets (a notice printed
  only on that branch). Both failures ship a block that is not what the tool prints.
- Never link a private file from a public one; it is a dead link for every user.

## Pitfalls

**Before any no-undo write to a user's REAL database (forget, delete), copy the
database to a dated file beside it and report its path.** A standing condition, not a judgement call.
Check the `-wal` is 0 bytes first (then the `.db` alone is complete), verify the copy
with `PRAGMA integrity_check` via `?immutable=1`, and name the file by the day it was
made, not by the brief's date. Then: dry run, confirm the plan names the expected
owner, apply.

**Scratch is shared with sibling sessions: delete only what this session created.**
List the scratch dir, name your own files, and leave everything else. Never keep a
helper you will re-run (a sabotage filter, a driver) inside a folder another agent owns
and will remove (a subst-mapped data copy, for example). Put it at the top of your own
scratch, or in `_private/spikes/`. Before sweeping,
move any verification script worth re-running (world builders, UI drivers) into
`_private/spikes/<topic>/` with a README of the run order; scratch auto-prunes, and a
list or driver that lived only there is gone for good. Sweep all of it in ONE delete
command, so the owner faces one approval prompt instead of several that can time out.

**Confirm a reported defect at the file-mechanics level before agreeing with it.** A
structural criticism of a plan is checkable in seconds when the affected module is pure
(path planning, sanitising, journal replay) — import it, run the disputed sequence, print
what lands on disk. That converts "unverified as a step" into "broken, here is the
output", or narrows an overstated claim to its real trigger. Agreeing from reasoning
alone gets the severity wrong in both directions.

**Reproduce a bug on the real command with the fix reverted, before writing it up.** Unit
tests prove the new guard works; only the reverted run proves the bug was real and shows
its true blast radius. Restore the code immediately and re-run both gates to confirm the
tree is clean — and if the reproduction dirtied a fixture, reset it before continuing, or
the next verification runs against damaged state.

**A test asserting on paths must normalise separators.** Comparing
`str(path.relative_to(root))` against a literal passes on one OS and fails on the other
for a project that claims to be cross-platform; use `.as_posix()` so the assertion reads
the same everywhere.

**Build fixture data at PRODUCTION dimensions when a test asserts on its stored size or
shape.** Helpers copied from a sibling test file are often deliberately reduced — a
three-element vector is enough to make a dot product come out right — and that reduction
silently invalidates any assertion on byte length, row width or serialised size, which
is exactly the assertion written when the stored artefact's survival IS the claim. Check
what a borrowed helper actually constructs before reusing it for a size assertion.

**Make a test fixture refuse to run against real user data structurally, not by
convention.** A test that builds the tool's own argument object inherits its defaults —
including the default data directory, which is the live database. Assert the sandbox path
is present inside the fixture builder so a future test cannot omit it silently.

**Answering "where were we?" from the docs, from memory, or from a past session's
transcript.** A session brief or a recalled conversation describes the repo as it was when
that session ended; every commit since is invisible to it, and its numbers read as freshly
checked. Conversation history is a POINTER to the project — which repo, which phase, which
files — never the source of truth on its state. Read the repo, run the tests and the
checkers, and report what the run said.

**When a figure you already gave turns out stale, open the next message with the
correction.** One sentence: what was wrong and where the bad number came from. Then the
corrected report. No apology paragraph, and never quietly restate the right numbers as
though the first answer had not happened — the user is deciding whether to trust the rest
of the report, and a silent fix removes the evidence they need.

**Adding a fourth file.** Three homes cover is / left / happened. A fourth means one of
them was not being maintained; fix that instead.

**Writing the roadmap as prose.** Phases, steps, checkboxes, Verify lines. Prose cannot
be ticked and does not survive a reset.

**Fix a wrong instruction IN PLACE; a correction printed below the broken version is not
a correction.** When a doc prescribes a command, a reader copies the first code block and
never reaches the caveat underneath — so replace the command itself and let the
explanation follow. The same holds for a rule and its exception: state the carve-out in
the same paragraph as the rule, not fifteen lines below, or the rule gets applied whole.
This is the most common way a documented fix fails to change behaviour.
