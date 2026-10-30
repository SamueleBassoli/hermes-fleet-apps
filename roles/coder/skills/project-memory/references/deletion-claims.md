# Auditing what a delete command really removes

For privacy deletes, purges, forget/erase commands, GDPR-style erasure, cache
invalidation — anywhere a doc promises that running something makes data go away.

An overstated deletion claim is uniquely dangerous: the code can be perfectly correct
while the promise around it is false, so no test fails and the contradiction lives in
prose until someone relies on it.

## Step 1 — measure what the current code deletes

Run it. Do not trace foreign keys by eye and do not read the schema comments; the
optimistic wording in the doc was written by someone who did exactly that.

On a throwaway database, print the counts of every related table before and after, and
print whatever the matching path consumes (the reference matrix, the index, the cache
key). The two questions are separate:

- does the subject stop being **recognised / served / found**?
- is the **stored artefact** actually gone?

The first can be true while the second is false, and that gap is the whole audit.

`ON DELETE CASCADE` on a join table removes the ASSOCIATION, never the referenced row.
Deleting a subject drops the rows linking it to its reference samples; the sample rows —
and the vectors, hashes or blobs inside them — survive in the table that owns them,
because those belong to the asset, not to the subject.

## Step 2 — the fork, and why the instinct is wrong

A gap between promise and behaviour has two fixes:

```
  A  narrow the doc to what the code does      feels like a retreat
  B  widen the code to match the promise       feels like integrity
```

B gets chosen on instinct. Measure it before choosing, with these two tests. If either
fires, A is the honest answer and B is a bigger lie than the one being fixed.

### Test 1 — can the code even identify the full set it would promise to delete?

Check whether the artefact table has any column attributing a row to the subject. Often
the ONLY attribution is the join table being deleted.

```
  subject learned from 3 inputs, appears in 50 indexed ones
  "delete orphaned artefacts"  ->  removes 3
                               ->  47 anonymous vectors remain
  the only way to attribute those 47 is to match the subject,
  which is precisely what the delete just removed
```

So B would delete a fraction while advertising the whole — and the new claim is harder
to qualify honestly than the old one.

### Test 2 — does deleting derived rows leave a freshness marker behind?

This is the one that causes real damage, and it is invisible to every existing test.

Pipelines skip work they believe is current: an `mtime` on the parent row, an etag, a
`processed_at`, a content hash. Delete the DERIVED rows and the parent keeps its marker,
so the re-indexer skips that asset **forever** while every reader sees it as legitimately
empty.

```
  DELETE FROM <derived>   ->  parent row stays, mtime intact
                          ->  is_current() = True   -> re-index SKIPS it, permanently
                          ->  children = 0          -> classifier reports "nothing here"
```

An asset that was a good reference becomes an asset the tool is *certain* is empty. Quiet,
permanent, and found months later by accident.

If B is still wanted after this, it must also clear the freshness marker or delete the
parent row — which widens the command's blast radius into a table it had no business
touching, and that widening belongs in the decision, not in the implementation.

## Step 3 — write the narrowed claim, and its cost

State what IS deleted in schema terms, then state the accepted cost in one plain line so
it is not rediscovered as a bug later: **"stop matching", not "no trace"** is the
usual honest shape.

Carry both measurements into the instruction file alongside the claim. Without them the
next session re-opens the question, reaches for B on the same instinct, and re-derives the
same two findings.

## Step 4 — park the real purge with its ordering constraint

A genuine "no trace" usually means deleting the parent/asset rows too, and it has a hard
ordering constraint worth recording even when unscheduled:

**The purge must run BEFORE the subject is forgotten, never after.** Once the attribution
rows are gone, nothing can find the subject's assets any more — matching was the only
thing that could attribute them.

That asymmetry generalises: an optional wider operation can be layered on top of the
narrow one, but the narrow one cannot be carved out of the wider one afterwards. Say which
order is possible on the parking-lot entry itself, not in the head of whoever wrote it.

## Step 5 — implementing the narrowed delete

Four properties, each of which has to be built in deliberately. They apply to any
irreversible destructive command, not only to privacy deletes.

### Delete the join rows EXPLICITLY; never rely on the cascade

`ON DELETE CASCADE` only fires while the engine's referential-integrity switch is on, and
that switch is typically set in a connection helper one function away — SQLite's
`PRAGMA foreign_keys` is off by default and per-connection. A delete whose correctness
depends on a pragma somebody else remembered to set is one refactor from silently
orphaning every association row, and orphans still join into the query that builds the
matcher. Issue the explicit `DELETE` on the join table and keep the cascade as a second
layer.

**Test it through a raw connection with the integrity switch OFF.** A test that opens the
database through the project's own helper cannot distinguish the explicit statement from
the cascade, so it stays green with the explicit statement deleted — the check passes for
the wrong reason.

### Refuse a near-match identifier; offer it, never resolve it

When the command is keyed on a user-supplied name and the key is case-sensitive unique,
two near-identical entities can both exist. Auto-resolving `Alice` to `alice` on an
irreversible command can permanently remove somebody the user did not name. Refuse by
name, list the near misses as a suggestion, and exit non-zero.

Fold conservatively: a SQL `lower()` is usually ASCII-only, so an accented name is simply
not offered. A missing suggestion costs a retype; a wrong one costs an entity.

### State that there is no undo, in the plan

A project where every other destructive command is journalled and reversible trains the
user to assume this one is too. If the command has no undo, the plan output must say so
in words — `--apply` is the only thing standing in for undo, so it has to be earned by an
honest plan.

Row deletes legitimately have no journal, and the reason is worth stating in the
docstring: a journal able to restore the subject would have to keep a copy of the very
data the command claims to have removed. That makes "no undo" a property, not an omission.

### Print what is NOT deleted, on every run

The narrowed claim lives in a roadmap or a wiki the user will never open. Put it in the
command's own output — what stays, and where — so the limits of the delete are visible at
the moment it runs. Assert on that line in a test, or it will be dropped as noise during
some later tidy-up.

## Step 6 — the GRANULAR delete: choosing the handle

After the whole-subject delete works, the next ask is always "remove ONE bad entry
(reference, grant, alias) without deleting the subject". That needs a public identifier,
and picking the wrong one is unrecoverable once users have copied numbers out.

### Build the LISTING before the delete, whatever the plan's order says

`<thing> --list` must ship before `delete --<thing> <id>`. Not merely because the ids are
otherwise locked inside the database, but because the delete cannot be acceptance-tested
without it: with no listing, the only thing to test against is a hand-seeded integer,
which proves the SQL works and proves nothing about the command being usable. The listing
is usually cheap — the store function feeding the existing delete often already SELECTs
the id and the caller discards it.

### The handle is the JOIN ROW's id, never the referenced asset's id

Check the join table's uniqueness constraint before deciding. `UNIQUE(subject_id,
asset_id)` and NOT unique on `asset_id` means one asset can be joined to two subjects at
once — which is exactly what a misdirected create looks like after someone repairs it by
attaching the same asset to the right subject without detaching the wrong one. An asset
id is then ambiguous on the precise case the granular delete exists to fix, and an
ambiguous handle on a command with no undo is not a handle.

Prove it rather than reading the DDL: insert the same asset for two subjects and watch it
succeed.

Every command touching the handle must publish the SAME id — the listing, the
whole-subject delete's plan, the JSON payload. Write one test that reads the id out of
one command and asserts the other names it; two commands with two id spaces is a handle
that only looks usable.

### A printed id is good now, not forever — so the consumer must plan first

Auto-increment integer keys are reused. SQLite hands the next insert the same rowid once
the row holding the highest one is deleted, so a number copied out of yesterday's listing
can name a different subject's entry today. This is a constraint on the DELETE, not on
the listing: it must plan first and NAME THE SUBJECT the id resolved to, so a stale number
is caught by the human reading the plan rather than by whoever it deleted. Record the
constraint on the unbuilt step, not in the head of whoever measured it.

### Print the full source path, never the basename

The user is choosing which entry to destroy permanently, and two assets in different
folders share a filename constantly. Show a quality or score column too where one exists:
the listing's purpose is finding the BAD entry, and without the evidence that
distinguishes bad from fine, the user is picking blind.

## Step 7 — the reverse cascade: re-processing silently destroys associations

Step 1 asks what a delete removes. Ask the mirror question too: **what destroys the join
rows without anyone calling a delete at all?**

A re-index/refresh helper that does `DELETE FROM derived WHERE parent = ?` before
re-inserting will take every association row with it by cascade. So re-scanning an asset
quietly unmakes a reference learned from it — triggered by a force-refresh flag, or by
anything that moves the freshness marker. The subject row survives with nothing attached:
still listed as known, absent from the matcher, matching nothing.

```
  replace_derived(parent)  ->  DELETE FROM derived WHERE parent = ?
                           ->  join rows CASCADE away
                           ->  subject row alive, zero associations
```

The listing command is the only place that state is visible, so name it there explicitly
(`0 reference(s) — matches nothing`). A blanket "weak: 1 item only" warning covering
everything below a threshold will describe an item that is no longer there.

Surface it before deciding whether to fix it — making re-processing preserve associations
is its own step with its own decision, and folding it into a listing change hides a
behaviour change inside a read-only feature.

## Step 8 — storing a NEW fact about a subject, so the delete still reaches it

Once the delete works, the next feature usually stores something new about subjects: a
remembered answer, a preference, a grant, an alias. Every such table inherits the delete's
rules, and the design sketch in the plan is almost always keyed on the wrong thing.

### Key it on the subject's ID, never on their unique name

A plan sketching `subject_set TEXT` (`'alice+bob'`) or any name-keyed column fails twice,
and both failures are reproducible on a real database rather than arguable from the schema:

```
  delete alice        ->  name-keyed row SURVIVES, still naming alice
  a different user is created as "alice"
                      ->  the stranger INHERITS the deleted user's stored decision
```

The second is the one that decides it. A unique constraint on `name` is unique only among
rows that CURRENTLY exist, so a name is a reusable handle — the same lesson as reused
rowids, one level up. Ids plus `ON DELETE CASCADE` cannot do either. Drive it: delete the
subject, re-create the name, and assert the stored fact does not match the newcomer.

The display string stays useful — put it in output and journals — but it is never the key.

### Deleting ONE member of a stored SET must take the WHOLE row

This is the bug a cascade creates rather than prevents, and only a test finds it. A fact
about a set lives in a member table; the FK cascade removes the one member row and leaves
the parent **alive with a shrunken set**:

```
  rule: alice + bob -> alice        delete bob (cascade only)
                                ->  rule: alice -> alice
                                ->  now fires on inputs with alice ALONE
```

A human decision silently changes meaning without the human. So the subject's delete must
remove every parent row they appear in — as owner OR as member — whole and explicitly,
before deleting the subject, and be tested with the integrity switch OFF so the cascade
cannot cover for the missing statement.

That makes two layers over one rule, which means naming which test owns which: deleting
the explicit statement does NOT fail the owner-case test, because the cascade legitimately
covers the owner. The test that owns the explicit layer is the integrity-switch-OFF one.

### Resolve names to ids with a pure LOOKUP, never with get-or-create

The write path usually has a name in hand and a `get_or_create_subject` helper already
imported, so the sketch reaches for it. Do not: every member of the set arrived from a
confident match, so the row already exists, and the create branch can therefore only fire
when something removed it — a delete run from another terminal while a queue built once
at startup still holds the old name. Creating it there resurrects a subject with zero
associations, which is exactly the state the granular delete refuses to manufacture. Look
the id up, and skip recording the fact when a member has gone.

### The delete for the new fact ships in the SAME phase

A store with no delete does not ship. The listing-before-delete rule from step 6 applies
unchanged, and the store-level delete is cheap to write alongside the table — doing it
then keeps the phase honest instead of leaving the inverse operation as a later step that
slips.
