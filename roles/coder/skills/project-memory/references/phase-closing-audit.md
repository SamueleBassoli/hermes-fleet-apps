# Phase-Closing Audit

The step that closes a phase usually reads "tests + wiki + README" with a Verify line of
nothing but the project's standard gates. That is exactly why it is dangerous: the gates
are green before the step starts and stay green through every finding, so the box gets
ticked on the assumption that the earlier steps covered it.

**What the gates are structurally blind to:**

| Gate | Proves | Cannot see |
|---|---|---|
| test suite | the code passes the tests written | a function nothing calls; an output line nothing asserts |
| doc checker | links, frontmatter, contradicted claims | a page that SHOULD mention the feature and never does |

So the audit asks coverage questions, not consistency ones. Ask which document *should*
mention this, not only which one contradicts it.

## Order

Run all four detectors **before fixing anything**. A fix landed mid-audit changes the
search space and the remaining detectors then run against a moved target.

### 0. Baseline both gates green

Run the suite and the checker first and record the numbers. Any red appearing later is
then unambiguously yours rather than inherited, which is the difference between a
five-minute fix and an afternoon of bisecting somebody else's mess.

### 1. Tests per file

```bash
pytest --collect-only -q 2>&1 | grep '::' | sed 's/::.*//' | sort | uniq -c | sort -rn
```

Count per file, **never assert a total**. A total is a number outside its own coverage
and drifts the moment anyone adds a file; the per-file table is what shows which area of
the phase is thin.

### 2. The zero-mention page

This is the detector that finds the stale page a contradiction search cannot:

```bash
for f in <doc pages>; do
  n=$(grep -ic '<feature keyword>' "$f"); [ "$n" = 0 ] && echo "ZERO: $f"
done
```

A page with **zero** occurrences of the phase's keyword is the candidate. Then judge each
hit by hand: a historical page (a spike log, a rejected-ideas list) legitimately never
mentions it, but a page describing how the tool behaves does not get to be silent about
a behaviour that shipped two phases ago.

The plain-language page is the usual casualty and the worst one to leave: it is the first
page a newcomer reads, it is written in prose rather than in claims the checker can
parse, and its outcome tables state old behaviour as fact. Check its `updated:` date
against the phase that last changed the behaviour it describes.

### 3. Functions with zero callers

Parse each source file, collect defined names, and search every source file for each name
used as a call or attribute. Exclude framework callbacks by name before reporting
(`__init__` and other dunders, `do_GET`/`do_POST`-style handler methods, registered
plugin hooks) or the output is mostly false positives.

For every genuine hit, also grep the **test** tree: a function with no callers in `src/`
but a test asserting it is the more interesting result, not the safer one.

### 4. Run the tool

Drive the real command — `--help` on the phase's commands, each refusal path, the exit
codes. Reading source does not find a tense that has moved on; running it does. Then
sweep every user-facing string for the deferral shape:

```bash
rg -n --no-ignore --hidden -g '!.venv' -g '!.git' \
  '"[^"]*(not yet|will be|cannot yet|for now|step [0-9]|coming|later)' src/
```

**Feed each NAMED DEFERRAL's input to the tool and read what it prints.** "The page shows
images only" is a deferral; "the queue says *nothing waiting* while a clip sits in it" is
a bug, and the two are told apart only by running the command with the deferred input
present. A capability the tool lacks must NAME itself in the output and point at the
workaround ("1 clip waiting — answer it with `assign`"); silence over a real file is the
same defect as a no-op run that prints nothing. Fix the silence inside the closing step
(it is small: count the deferred inputs, print them), keep the capability deferred, and
drive the workaround command on the same artefact before documenting it — a fallback
that refuses the file it is prescribed for is a second bug in the docs.

Check the exit code of the tool, not of the pipeline: `cmd | head; echo $?` reports
`head`'s status, so a command that exits 2 on a bad argument reads as success. Redirect
to `/dev/null` and test `$?` directly.

**Every sample output block the audit adds to a doc is pasted from a run, never
composed.** Build a throwaway library in Temp with the neutral names the docs already use
(`alice`, `hiking-back.jpg`, `/path/to/library`), run the exact command line the doc
shows, and paste stdout verbatim — that satisfies the no-real-data rule without inventing
the output. A block written from memory of what the command "prints" drops the lines the
code adds on the branch the sample happens to take (an unknown-subject notice, a near-miss
hint), and the doc then promises quieter output than the tool gives. Delete the scratch
library in the same command.

### 5. Guard what the audit fixed

A doc sample corrected in the audit — a required flag that was missing, a verdict string,
an exit code — is a claim the checker was not watching, which is why it rotted. Add one
checker claim per corrected fact, anchored to the code line that makes it true (the
`required=True` on the argument, the literal in the journalled record), then sabotage each
from a finally-restore script and confirm its own claim fails. The sample cannot drift
again without a red gate.

## Which ending the step gets is decided by the audit, not in advance

A phase-closing step whose findings are all private (wiki, roadmap, the instruction file)
ends at the log entry with `git add -A --dry-run` printing nothing. The moment one finding
lands in a public file — a README section the zero-mention detector found — the step ends
at a commit, the counts move, and the version line is re-derived after it. Run the
detectors first and read the dry-run output before choosing; the brief's guess about which
case applies is a guess.

## Dead code is deleted, not documented

When the caller scan finds a function nothing calls, remove it. Do **not** write a note
explaining why it exists.

- **A passing test is not evidence that code is reachable.** The test is precisely what
  made it look alive in every earlier audit — correct, green, and wired to nothing.
- **Delete the fields only that function read.** A property removed on its own leaves the
  attributes it consumed being written and never read, which is the same defect one layer
  down and the next audit has to find it again.
- **Distinguish it from the case where a command is waiting.** Code that is unreachable
  *because the step exposing it has not shipped yet* stays, and the step that will use it
  is named. Code with nothing scheduled to reach it goes. Version control holds it if a
  caller ever appears; the wiki does not have to.

## Deciding a known gap: test it or write down why not

When the phase inherits an untested path from an earlier step, the choice is not
judgement — it is arithmetic. **If a seam already exists, writing the tests is less work
than writing down why there are none.** The excuse has to be accurate, has to be swept
for when the code changes, and convinces nobody; the tests are finite and end the
question. Prefer the note only when driving the path would mean building infrastructure
the project does not otherwise need.

## Write the close-out as findings, not as a tick

On the step itself, record what the audit found in each category and — explicitly — that
both gates were green throughout. A future session reading a bare `[x]` cannot tell a
phase that was audited from one that ran out of steps, and will trust the gates the same
way this one nearly did.
