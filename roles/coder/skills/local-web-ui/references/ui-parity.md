# UI parity: everything the CLI does, the window does too

Once a window exists, the CLI-first rule (SKILL.md) says the window may only call the
CLI; parity says the window must eventually reach every CAPABILITY the CLI has. Count
capabilities, not flags. The owner confirms every "not applicable".

## Audit (no code)

1. List the CLI surface from the parser itself (`grep -n "add_parser\|add_argument"`),
   plus each option's `help=` and each command's docstring for what it really does.
2. List what the window reaches: the Api methods, every `api().` call in the page JS, and
   fixed values the window passes (a hard-coded depth or count is a gap).
3. One row per capability, three buckets:
   - already in the window (one line);
   - gap: a todo with the CLI command, the likely window home, and a *Verify:* line (the
     observable proof, including undo);
   - not applicable, with ONE line why. Valid n/a: only a program needs it (`--json`,
     progress feeds), the window already replaces it, or a repair tool. Mark doubtful ones
     "candidate n/a, owner decides".
4. Look for silent first-run traps while auditing: a window that needs a flag the CLI
   defaults, or a fixed limit that finds nothing and says nothing. Rank these first: a new
   user hits them before any feature.
5. Show the owner the list; they accept or overrule each n/a and set the order. Record
   their reasons next to each decision.

## Guard test

Reuse the list the bridge already ENFORCES; never add a second parity table (two lists
drift, and only the enforced one is true).

- "window" = the bridge's allow-list (`ALLOWED`: command -> options). "n/a" = a dict
  beside it in the same file (`NOT_IN_WINDOW`), keys `"cmd"`, `"cmd --opt"` or `"--opt"`,
  value = one line why.
- The test walks `build_parser()` (subcommands, longest option string per action, skip
  help and positionals) and fails, naming the item, on: (a) in neither list, (b) in both,
  (c) blank reason, (d) an entry the CLI no longer has, (e) allowed but the Api never
  sends it.
- Allowed-but-unsent entries are usually dead allow-list entries: propose moving them to
  n/a (smaller attack surface, no screen changes) and add a test that the bridge refuses
  them.
- Write the checker as `problems(parser, allowed, na, app_src) -> [msg]` taking its inputs
  as arguments, so every sabotage is a permanent test, not a one-off script. Still prove
  it once on the real files (the qa role's `guard-verification`).

## Shape a parity screen before coding it

The owner sees where the button lives, what they click and how undo works BEFORE any code:

- A static HTML mock that links the window's REAL stylesheets and reuses its real classes
  and copy, rendered in both themes.
- Numbered panels in the user's order: start, doing it, the error case, undo. Outline new
  parts with a dashed box and a "new" tag.
- Synthetic thumbnails (inline SVG) and invented paths only.
- Copy wording from the real JS; a mock that contradicts the window misleads.
- Headless Chrome screenshot per theme, look at it, give the owner both paths. Report as
  panel-by-panel bullets, then the decisions they must make, recommended option first.
- State what the backend already does and any limit of the design.

## Shape a silent-trap gap (no new screen)

1. Reproduce it with the real CLI on a throwaway tree and a throwaway `--data-dir`.
2. Report "what goes wrong today" in plain words with a small diagram, the exact message
   or missing item, and any worse trap next to it. Never report a trap as read from the
   code alone: build a world that exercises it and run it to its end. Run the even case
   and the lopsided case.
3. Outcome rule: stops or warns = no change; silent wrong result = a todo with the
   measurements, ranked ahead of missing buttons.
4. Fix in the engine/CLI first: a fixed limit must REPORT that it cut something (a key in
   the JSON plus one human line naming the flag); the window then offers the next step on
   request instead of raising the default.
5. When the trap gets its fix, replay the measured world through the built rule before
   reporting.

## Check the item's premise in the code before shaping it

A todo that names a number to show assumes the number answers the question. Read what the
CLI field really is first. If it cannot answer the question, say so, correct the todo, and
offer the measure that does (CLI first, with a spike that plants a known-bad item and must
catch it).

## Lists the window shows must survive a closed window

A list kept only in page memory is a bug: the link is gone next launch. Ask whether the
stored data already implies it; if yes, add a read-only CLI command that rebuilds it and a
test that it writes nothing. Find files the tool moved since by CONTENT, never by name. If
it needs new storage, do not add it silently: say so on the page and tell the owner.

## Build and close a parity item

Order: tests first (red) -> CLI change -> bridge allow-list -> Api -> page -> docs (README,
CLI reference, the agent's own skill) -> full gate -> real-window run in both themes ->
look -> report -> commit on the owner's ok.

- **Closed means two things:** the window does it AND the README's "command line only"
  note for it is gone. A test that pins the README wording keeps it closed.
- **Plain words include folder and file names.** Internal folder names and database file
  names are jargon on a page.
- **A limit found while verifying is reported, not silently fixed.**
- **Numbers from the page are clamped in the Api**: not a whole number -> omit the flag so
  the CLI default applies; else clamp to the CLI's own floor and ceiling.
- **Deleting by id from the page: names travel, numbers do not.** Store ids get reused.
  The second click sends the names the page SHOWED; the Api re-reads the plan and applies
  only if it still matches.
- **A delete that cascades says so in its confirm.**
- **A command that writes at once gets a plan step before the window exposes it.** If the
  CLI lacks a dry run, offer adding one (default = plan, `--apply` = do it), then grep
  EVERY caller (tests, other screens, agent skill and instruction files, docs) and add
  `--apply`: an old caller now silently does nothing.
- **Elements the page script creates are held by reference**, not looked up by id.
- **Screenshot the longest dynamic copy** (armed button text, warnings) in both themes.

## Pitfall

The roadmap or log may live in a gitignored private folder: "record and commit" then means
write it and say plainly there was nothing to commit, rather than inventing a commit.
