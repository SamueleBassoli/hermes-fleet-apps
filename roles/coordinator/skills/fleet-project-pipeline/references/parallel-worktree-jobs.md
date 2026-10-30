# Parallel lines of the same role (git worktrees)

Use when the owner wants more done at once and the jobs touch different parts of one repo.
Several coder cards can run at the same time; worktrees keep them off each other's files.

## Decide first

- One line = the main tree, or one worktree + branch. Parallel only if the jobs share few
  files: the small job on main, the big one in a worktree.
- Same-file edits in both lines (CLI entry, README, CHANGELOG) are fine: the coordinator
  resolves them at merge.
- Three lines (main + two worktrees) is the practical ceiling; a fourth guarantees
  conflicts in the hot files. Show the owner the lines as a small column schema: what runs,
  what waits on what.
- When a line frees up, refill it with the next ticket that does not depend on an unmerged
  branch. A ticket half-dependent on one: split it, start the independent half now.
- A line whose code another line imports: its brief freezes the contract (add commands
  only, no renames, no change of the data envelope); the importing line lists every
  shared-file edit in REPORT so the merge is mechanical.
- Every parallel brief says "add, don't reshuffle": new code in NEW modules, only the
  registration lines in shared files, no moves; it names the hot files the other lines edit.

## Deadline run from a fresh repo

1. Say the real limit up front in one line (e.g. hardware busy, one feature at risk); ask
   the one question that changes the plan, and do not wait for the answer.
2. A small foundation card on main FIRST: research the external tool's real flags, pin
   versions, skeleton, lock file, a FAKE of the external engine for tests, and
   `docs/ARCHITECTURE.md` as the frozen contract (module ownership per line, stub
   signatures, data layout, API). Order it so the contract is written right after the
   research: a worker that hits its context limit with stubs but no contract stalls
   every line.
3. Create the worktrees from current main at once; each line card is a child of the
   foundation card and its first step is `git merge --ff-only main`.
4. One qa card per line as its child, created in the same batch, after `COMMON-RULES.md` and
   `QA-RULES.md` are committed. An "Unattended run" schema in CHECKLIST and one scheduled report.

## "What's next?" after a release

1. Read CHECKLIST (unticked items), the SPEC's "Later" and "does not do", open qa LOWs. Tick
   what is already done in fact.
2. Sort into lines: LOWs and polish on main, each new feature in its own worktree, a UI
   feature as designer -> coder -> qa on one line. Max 3 lines.
3. Say what should NOT start yet and why (features that need weeks of real data; items
   that break a v1 rule are the owner's decision, not polish).
4. One message: lines as letters with one line of benefit + cost each, your pick, ask
   which to run. Then worktrees, briefs and the CHECKLIST section in one commit, all
   cards in one batch.
5. Features touching the owner's data tune on a scratch COPY and show before/after; any
   backfill is a dry run for the worker, the write is the coordinator's with the owner's ok.
6. A brief that adds a model names the exact model, version, file and licence, checked to
   be the newest. Each model swap has a stop gate: measure it on real data against the
   current one, keep the old one if the new one is worse.

## Setup (coordinator, before dispatch)

```bash
git -C <abs repo> worktree add -q -b <branch> <abs repo>-<tag>
```

- Pass ABSOLUTE paths to every `git -C <repo> worktree add|move` argument: relative paths
  resolve against `-C`. Check with `git worktree list` after each command.
- Share heavy git-ignored folders (models, `node_modules`) with a link instead of copying
  gigabytes: a directory junction on Windows (PowerShell `New-Item -ItemType Junction`;
  `cmd //c mklink /J` from git-bash silently does nothing), a symlink elsewhere. Create it
  yourself before the card, after checking in the code where it looks for those files.
- Reuse the main tree's virtual environment: with cwd = the worktree, `python -m` puts the
  worktree's package first. Prove it: `import pkg; print(pkg.__file__)` points INTO the
  worktree. No second install.
- Briefs stay in main's `jobs/` and are cited by absolute path; each worker writes its
  REPORT in its own job folder (no merge conflicts).
- Append-only shared files (index pages, logs, CHANGELOG) conflict at every merge: lines
  append only; resolve as the union of both sides.
- Add the jobs folder to the linter's ignores before dispatch, or one worker's scratch
  turns lint red for every other line.
- The owner's real app data: snapshot it before dispatch (file list, sizes, hashes), fence
  it in the rules, give every runtime test an isolated data dir, and compare at each card
  check (judge dates, sizes and hashes, not a raw `ls` diff).

## Brief rules for a worktree job

- Name the folders it may write and forbid the rest; never push, merge or rebase (the
  coordinator merges). Exception, stated in the brief: rebasing its own unshared branch.
- The shared environment path, the `__file__` check, "never delete through a linked folder".
- Realistic data: a scratch copy of the real data home, its env var set inline in every
  command; the real home is read-only.
- A feature that depends on an unbuilt ticket is "shown disabled, coming with <ticket>".

## Inserting or holding a job

- A feature asked for mid-line goes in BEFORE the reviews: create it with `--parent
  <current head>`, `hermes kanban link <new> <review card>`, and comment each review card
  on what extra to check. Never recreate the review cards.
- `link` refuses a child that is already running: then reclaim and archive that review card
  and create a new one with `--parent <new job>`.
- `hermes kanban block` refuses `todo` cards. To hold one until a merge lands, comment a
  wait condition (`git merge-base --is-ancestor <sha> HEAD` every 60 s, max 30 min).
- A qa card that completes with FAIL still releases its children: check what started, hang
  the fix + recheck pair after it, `unlink` the later stage and `link` it to the recheck.
- Never let a card that RUNS the product from main's tree (a live qa run, the operating
  agent) overlap a coder editing that tree: chain them on the same line.

## Side effects of live tests in a worktree

- A product that scans for git repos sees each worktree as a new project (a worktree's
  `.git` is a file). The product should skip `.git` files pointing into `.git/worktrees/`.
- A worker testing a feature that creates kanban cards creates REAL cards that reach the
  owner's chat: say it was a test, and add a qa check that the product path does not notify.
- Headless workers often cannot recursive-delete or force-kill. Brief line: "if recursive
  delete is blocked, remove files one by one, then `rmdir` bottom-up; list what you could
  not remove in REPORT's first lines". Clean the rest yourself at each card check.
- Workers cannot write protected instruction files (`AGENTS.md`, `SOUL.md`): the brief asks
  for the exact text in REPORT, and the coordinator puts it in place.

## Merge and cleanup

1. In the finished branch's worktree: `git merge --no-edit main`, resolve, full suite
   green, commit. Pitfalls when taking "both" sides of a code conflict:
   - sibling dispatch blocks sharing one trailing `return`: the first falls through;
   - the same flag added by both lines with different meanings: keep one, merge the help;
   - a delete written on one line must cover tables the other line added;
   - an import removed on one side and still used on the other: grep for it;
   - both sides extending one `from x import a, b` line: write the union.
   Many hunks: a one-shot resolver script that exits if the hunk count differs from the
   plan. Real code hunks get a qa card on the merge commit before main receives it.
2. Merge into main only when no card works in main's tree (an agent editing paths the branch
   never touches does not block). `git merge --no-ff --no-commit <branch>`, suite + lint,
   then `git add <resolved files>` and commit; never `-a`, which sweeps in another agent's
   uncommitted files. A job split into legs merges once, after its last leg.
3. One line at a time. Read the test count from a run without `-q`. The whole gate as one
   background command:
   `set -o pipefail; git merge --no-ff --no-commit B && pytest > log; P=$?; ruff check . > log2; R=$?;`
   `if [ $P -eq 0 ] && [ $R -eq 0 ]; then git commit -m "..."; else git merge --abort; fi`
   After all lines: merged count = base + each line's added tests; less means a merge
   dropped a test file. After a UI line: restart the owner's server and look at the new view.
4. Cleanup once the merge is verified: remove the link first (deleting the link, never
   recursively through it), then `git worktree remove <wt>`, `git worktree prune`,
   `git branch -d <branch>`; check the shared folder still has its size. A folder that
   stays "busy" is some process's cwd (often your own shell): `cd` out, `rmdir`, prune.
   Data a line left outside the repo (test sets, caches): keep it, tell the owner its size
   and which part can be re-downloaded.

## Owner away

An "Unattended run" section in CHECKLIST (ordered steps, merge order, what waits for the owner)
plus one scheduled report. qa FAILs get fix + recheck cards without asking; each
completion: verify, merge what passed, start the next step, one short note. A real-data
write announced earlier as "after qa unless you say wait" counts as the owner's ok: run it
with a backup and report counts. Report: What's new / Verified / To know / Cleanup
/ Left.
