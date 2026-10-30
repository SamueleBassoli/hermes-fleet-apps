# Migrating a schema that already ships

For adding a column, relaxing a constraint, or widening a table in a project whose
database is already on a user's disk. Distinct from designing a new table: the failures
here are all silent, and most of them surface one release later.

## The rule that generates most of the others

`CREATE TABLE IF NOT EXISTS` creates a table that is MISSING and is a silent no-op on one
that exists in the wrong shape. No error, no warning. So a startup script that runs the
current schema text against every database migrates a new table into existence and does
nothing whatsoever about a changed column — and the mismatch surfaces much later as
`no such column` in whichever feature reads it first.

That asymmetry is the reason a version stamp exists at all. State it in the code beside
the stamp, because the next person to add a table will correctly observe that no
migration was needed for theirs.

## Step 1 — the version gate's "absent" branch must migrate too

The seductive reasoning: *absent means very old, the schema script just ran, so everything
is current — stamp it and return.* The first clause is true and the second is false, for
exactly the reason above. A pre-stamp database arrives with the old table shape, gets
stamped as current, and every later open fails on a column nothing ever added.

Make the absent branch run the migration and then stamp. Migrations must therefore be
**idempotent** — check for the column and return early:

```python
cols = {r["name"] for r in con.execute("PRAGMA table_info(<table>)")}
if "<new_col>" in cols:
    return
```

That costs one pragma on a database that needed nothing, and it is what lets the same
function serve the absent branch, the older-version branch, and a re-open.

Register migrations in a dict keyed by from-version rather than a chain of `if`s, so a
missing one is a lookup miss with a clear refusal instead of a branch somebody forgot.
Keep refusing a version with no registered migration: silently opening a database the
code has outgrown is the failure the stamp exists to prevent.

## Step 2 — schema that names a NEW column cannot live in the always-run script

An index or trigger referencing the added column will execute against the OLD database
*before* the migration that adds it, because the schema script runs first. The error is
`no such column`, raised inside the connect helper — so the release meant to upgrade the
database is the release that makes it permanently unopenable.

Split it: the always-run schema, then the version gate and its migrations, then a
second script holding anything that depends on the new shape. Say in a comment that the
split is load-bearing and not tidiness, or it will be folded back.

## Step 3 — rebuilding a table (the only way to relax a constraint)

SQLite cannot drop NOT NULL or add a CHECK in place. Create new, copy, drop, rename.
Three things to get right:

**Name the id column explicitly in the copy.** If the id is a public handle the user can
copy off a screen — a reference id a delete command accepts, an invoice number — a rebuild
that lets rowids renumber silently moves every written-down id onto a different row. This
is the single most destructive thing a migration can do and nothing fails at the time.

**Turn the integrity switch off for the rebuild and back on after.** `ALTER TABLE ...
RENAME` with foreign keys ON rewrites other tables' references to point at the new name,
and `DROP TABLE parent` with them ON is an implicit DELETE that fires every
`ON DELETE CASCADE` child: rebuilding `sample` would wipe every reference row.

**Read the new table's definition out of the current schema text** (regex the
`CREATE TABLE ... (` block) instead of retyping it in the migration, so the rebuilt table
cannot drift from what a fresh database gets. Re-run the schema script after the rebuild:
the dropped tables took their indexes with them.
Restore it in a `finally`, then run `PRAGMA foreign_key_check` and refuse if it reports
rows — a migration that orphaned something must not be stamped as successful.

**Wrap it in an explicit transaction with a rollback on exception**, so a failure leaves
the original table rather than a half-copied one.

## Step 4 — prove it on a REAL old database, not on a unit test

Build a database with the OLD schema text (paste the previous table definition into the
current script), fill it with rows whose ids are deliberately NOT 1, 2, 3, then open it
with the new code and assert:

- the version is now current, and the new column exists
- every row survived **with its original id**
- pre-existing rows got the intended default for the new column
- `PRAGMA foreign_key_check` is empty and the integrity switch is back ON
- each new constraint actually refuses its violation
- re-opening is a no-op, not a second rebuild

Gapped ids (7, 42) are the whole point: sequential ids let a renumbering rebuild pass.

## Step 4b — ids the user copies must be permanent (AUTOINCREMENT)

A plain `INTEGER PRIMARY KEY` hands the highest freed id out again: delete the newest
row, insert, and the old number names a different row. Any id a command prints for a
human or agent to paste later (sample ids, reference ids) needs `AUTOINCREMENT`. Test it
before building on the ids: throwaway db, real store code, delete top, insert, compare.
It cannot be added in place, so it is a Step 3 rebuild. State the honest limit: the
counter starts at today's max, so a number freed before the upgrade above that max can
repeat once. Existing tests or docs that assert "ids get reused" are now wrong: rewrite
them to assert the new guarantee and flag the rewrite in the report.

## Step 4c — an upgrade of a user's real file: backup, prove, stamp

Order inside the connect helper, before the schema script touches anything:

1. **Backup only when there is something to upgrade** (existing tables, stamp missing or
   older). Use `sqlite3.Connection.backup` (includes un-checkpointed `-wal` changes),
   name it `<db>.schema<N>-backup-<date>.db` beside the db, never overwrite (`-2`, `-3`),
   verify integrity + per-table row counts. Copy fails or mismatches -> delete the
   half-written file and refuse; no backup, no upgrade.
2. **Prove inside the transaction, not after**: hash every column of every row per table
   (rowid order) before and after the rebuild, plus `foreign_key_check`; any difference
   raises, rolls back, the db stays at the old version.
3. **Run migrations as a loop** `for v in range(found, CURRENT)`, and test it from the
   OLDEST stamped version: with one from-version the loop is untested — sabotage
   replacing it with a single call passes until a stamped-oldest test exists.
4. **Read-only commands (`mode=ro`) never upgrade or back up** — test that a reader on
   the old version leaves it byte-identical with no backup file.

Prove on COPIES of each real db (copy first; never open the original), reporting a
before/after table: version, autoinc flags, rows per table, id-list hash, all-column
hash, embeddings hash, integrity, orphans, index count, upgrade time, second-open time,
backup verified; then an id test on a throwaway copy of the upgraded db, then the
product commands (listing ids, main read command) still give their known numbers.

If the user's app may run from the working tree, uncommitted schema code upgrades the
real file the moment it starts: check no app process runs, and tell the user not to
restart it before the commit ok.

## Step 5 — SQLite NULL semantics will defeat your uniqueness constraint

**Every NULL is distinct in a UNIQUE constraint.** So when a column becomes nullable to
make room for a second variant, the existing `UNIQUE(owner_id, thing_id)` silently stops
constraining every row whose `thing_id` is NULL — the new variant can be inserted twice,
and `INSERT OR IGNORE` cheerfully inserts rather than ignoring. Add a second unique index
over the other column pair, and write a test that calls the store twice and asserts one
row.

Use a CHECK for exactly-one-of rather than a comment:

```sql
CHECK ((a_id IS NULL) <> (b_id IS NULL))
```

A row set in both columns would otherwise appear twice in any query that UNIONs the two
halves, under one id.

## Step 6 — one id space when a thing gains a second variant

When an entity can now come from two sources, resist a second table. The tie-breaker is
whether anything **publishes an id to the user**: two tables mean two rowid counters, so
there are two id 5s, and the number a human copies off a listing stops identifying one
thing. One table with a nullable column per variant keeps one id space, so no command
needs a flag saying which kind it is about.

This propagates into the read paths, and each is a silent wrong answer if missed:

- **A function returning "the id of the underlying row" must switch to the JOIN row's
  id.** The two variant tables have independent counters, so a list mixing them names
  nothing. The join row's id is also the one the delete command accepts, which makes
  every downstream assertion a statement about the thing the user actually handles.
- **UNION the two halves; never inner-join both.** A row points at exactly one, so a
  join against both returns nothing at all.
- **Order by a stable key, not by the display name alone.** A UNION's row order is
  otherwise whatever the query plan produced, so any test indexing a row passes by luck.
- **COALESCE any column that now comes from either side.** A listing reading
  `det_score`/`size`/`created_at` from the original table alone returns NULL for every
  row of the new variant — and that blank lands on precisely the variant the user has
  least reason to trust from memory. Add a `kind` expression in the same SELECT so
  callers label rows without re-deriving it from which id is NULL.
- **A count used by a refusal must count both halves.** A last-one-left guard that joins
  only the original table sees zero for an entity made entirely of the new variant, and
  happily empties it — manufacturing the exact state the guard exists to prevent.

## Step 7 — the test-helper fallout

Helpers in the existing suite coerce the column that just became nullable (`int(row[id])`)
and will raise on the new variant. Fix the helper to pass NULL through rather than
teaching each test to avoid it, and have it surface the `kind` column so tests assert on
the variant directly.

Expect a handful of existing tests to fail on the CONTRACT you deliberately changed
(a returned id that now means something else). That is the suite doing its job — rewrite
the assertion and put the reason in the docstring, so the next reader does not "restore"
it.
