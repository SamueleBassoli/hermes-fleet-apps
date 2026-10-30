# Verifying guards by sabotage

For any project where a rule is enforced in code and a test or checker claims to catch
its removal. The pass answers one question per guard: **if this guard vanished, which
named test fails?**

"A test failed" is not verification. *Which* test failed is.

## The procedure

1. Enumerate the guards the change added — every refusal, every gate, every key a query
   is keyed on, every disclosure line a test asserts.
2. Write one injected break per guard, in isolation. Never two at once.
3. Run the suite after each; record the set of tests that did not pass.
4. Restore the file from an in-memory copy of the original, in a `finally`.
5. Read the report: each guard must fire the test written ABOUT that guard.
6. Check `git status --porcelain` at the end, whatever happened.

Use `templates/sabotage_pass.py` rather than hand-typing the loop each time.

Scope the run to the relevant test files while iterating (seconds, not minutes), then run
the full suite once at the end.

**Never run the pass with a stop-on-first-failure flag (`-x`, `--exitfirst`).** An
unrelated test that sorts earlier then aborts the run before the guard's own test is
reached, and the harness reports "the wrong test failed" for every injection — a false
negative that looks like missing coverage. A pass that stops early cannot distinguish
"the wrong test failed" from "the right test never ran", so let every failure be named.

## Break each guard two ways, not one

| Injection | Proves |
|---|---|
| delete the guard | the suite notices a missing check |
| make the guard vacuously TRUE (`if False:`, `<= 0`) | the suite notices a check that silently disables the feature it protects |

An off-by-one in a threshold is the common real bug and only the second form catches it:
a `remaining <= 1` refusal changed to `<= 0` still refuses nothing, and a test that only
checks "the refusal exists" stays green.

## When a sabotage changes NOTHING

Green after an injected break looks like proof the test is redundant. It is almost always
proof the sabotage was, or that the guard is shadowed. Five mechanisms, in the order they
occur:

### 1. The injection is inert by ORDERING

A destructive statement placed after the statement that supplies its input reads rows
that are already gone, matches nothing, and runs as a no-op.

```
  DELETE FROM link WHERE subject = ?              <- runs first
  DELETE FROM sample WHERE id IN (SELECT sample_id <- subquery now matches nothing
                                  FROM link WHERE subject = ?)
```

Re-order the injection so its inputs still exist, then re-run.

### 2. The FIXTURE makes two values coincide

A fixture that joins every row it creates runs both id counters 1, 2, 3 in step, so
swapping one id for the other prints identical numbers. Force the values apart in setup —
create one row that is deliberately never joined — and ASSERT inside the fixture that they
differ, making the divergence its stated contract rather than an accident of insertion
order.

### 3. The FIXTURE leaks the value through another channel

An assertion that the output NAMES something passes on any other field carrying the same
string. A subject's assets filed under a folder named after the subject make "the plan
names the subject" true from the path, so deleting the naming changes no test.

Fix it in three places at once:

- neutral fixture data — keep the asserted value out of every other printed field
- an assertion in the fixture that it appears nowhere else
- an assertion in the test anchored to the specific line that makes the claim, not to the
  whole captured output

```python
attribution = next(l for l in out.splitlines() if "belongs to" in l)
assert attribution.strip().endswith("alice")
```

### 3b. The anchor never MATCHED

A `find` string absent from the file leaves the source untouched, the gate green, and
the report reading "redundant". Two causes: the anchor was written against the first
occurrence of a line that exists twice (two threshold comparisons, two render paths) and
the harness replaced the wrong one — or a multi-line anchor written with `\n` was run
against a CRLF file, where it matches nothing. The harness must read with
`open(..., newline="")`, convert the anchor's endings to the file's, and report
**NOT APPLIED** as its own outcome, distinct from **NOT CAUGHT** — the two are opposite
findings printed by the same green result.

### 4. The sabotage did not COMPILE

A broken edit makes every test ERROR before running. A harness scraping only `FAILED`
lines reports nothing — indistinguishable from a redundant test. Count errors, collection
failures and non-standard exit codes; report "exited without naming a test" explicitly.

### 5. A SECOND guard downstream already refuses the case

The guard is real and the test is real, but a later check in the same path rejects the
input anyway, so deleting the first one changes no outcome. This is the only mechanism
where the sabotage worked perfectly and the code is still fine — and it is the one most
often misread as "delete the redundant check".

The recurring cause is a **sentinel value that shares a namespace with user data**: a
reserved folder or bucket name (`_unknown`, `_review`, `default`) travels through the same
field as a real subject name, so the lookup that resolves it returns nothing and refuses
the operation before the dedicated gate is ever consulted.

Ask the right question — **not "is this test redundant" but "is this LAYER reachable"** —
and answer it by driving the state that would reach it, never by reasoning:

- **Reachable** → the FIXTURE is wrong, not the layer. Push it into that state (create a
  subject under the reserved name), assert in the test that the state holds, and re-run.
  The guard is now the only thing standing between the input and the wrong outcome.
- **Not reachable by any input** → the layer buys nothing. Delete it and keep one guard.

Record the finding in the test's docstring with the reason the fixture is unusual, or the
next session simplifies the setup and silently un-tests the gate.

## Sabotaging a checker claim that greps for a call

A doc-checker claim anchored on a helper's name (`cmd_x\((?:(?!\ndef )[\s\S])*?helper\(arg\)`)
is sabotaged by replacing every CALL inside the bounded function with `pass` while
leaving the `def` where it is. Deleting the definition too makes the file fail to
import, which is mechanism 4 above, and it can also let the pattern keep matching the
`def` line's own text. Assert in the script that the call string is absent from the
sliced-out function body before running the checker, so an injection that missed one
indentation variant is caught as a bad sabotage rather than read as a loose claim.

## A project gate that is red for cases outside your diff

A standing sabotage harness accumulates cases; when it exits red after your change,
prove each red case is not yours before reporting, rather than calling it "pre-existing":

- **NOT APPLIED** — the find string is gone. Check it at the last commit:
  `git show HEAD:<file> | grep -cF '<find>'`. 0 there too means the case went stale
  before your step.
- **NOT CAUGHT** on a file your diff never touches (`git diff --stat`) is not yours. One
  on a file you DID touch must be re-run on HEAD (stash, run that case, pop) before you
  call it old — say "most likely old, not proven" until then.

Do not repair them inside the feature step; record each as an owed step in the log, with
the check command, so the gate's exit code means something again.

## Proving a command "writes nothing" on SQLite

Snapshot before and after: main db bytes and mtime, the `-wal` CONTENT (treat a missing
WAL and an empty one as the same state), the data dir's file list excluding `-wal`/`-shm`,
and every input file's bytes. A read-only open of a WAL database legitimately creates
empty `-wal`/`-shm` side files, so a test asserting "no new files" fails on a correct
reader. Call `gc.collect()` before each snapshot in an in-process test: an earlier
command's connection that is closed only by garbage collection checkpoints its own WAL at
that moment and makes the db change between snapshots for a reason that is not the
command under test. Also test "no database yet" separately — a reader must not create one.

## Restoring, and why a script

Run the pass from a script, not from a long-lived interpreter session. A kernel killed by
a timeout mid-iteration leaves the injected break in the source — discovered later as an
unexplained modification, or committed.

- read every target file once, keep the text in memory
- restore inside `finally` after each iteration AND in an outer `finally`
- verify the tree afterwards with `git status --porcelain`, every time
- re-run the full suite once the pass finishes, before trusting anything

## Capturing the result

Write the guard-to-test mapping into the step's own record: `the --apply gate →
test_a_dry_run_removes_nothing`. A future session reading "verified by sabotage" with no
mapping has to redo the entire pass to learn what is actually covered.

Where one test legitimately covers two layers, say so in that test's docstring — it
passes with either layer deleted, so it is evidence of neither, and without the note it
reads as the proof of both.
