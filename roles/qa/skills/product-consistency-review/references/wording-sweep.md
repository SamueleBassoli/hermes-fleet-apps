# Wording sweep: applying a glossary across window, CLI and docs

A "words only" step: one idea, one word, everywhere a user reads it. No layout,
no logic. Shape it before touching anything; the shape is mostly about what is
NOT renamed.

## Inventory (one kernel cell, no repo writes)

1. Load the glossary, the target files and the review's "small changes" list.
2. For JS/Python UI files, extract string and template literals with a regex
   and match them against the OLD words. That gives a per-file count for the
   shape and the exact lines to edit.
3. For CLI files, AST-walk the string constants (skip docstrings and SQL) and
   keep those with a space that hold an old word: `print(`, `help=`,
   `description=` text is user text, the command name is not.
4. Grep the WHOLE `src/` tree, not only the files the brief names. User
   sentences hide in config constants (refusal messages) and the desktop
   bridge (error strings, `--data-dir` help).
5. `rg -c` the old phrases across `tests/` to list every test that pins a
   string, including tests that pin README/doc wording: those are rewritten in
   the same step, or the full run flags them late.
6. `rg` the CLI's human banners ("DRY RUN") in docs and the agent skill: if
   the printed line changes, every doc that quotes sample output changes too.

## Never renamed in a words step (state it in the shape, with the reason)

- command names and flags: scripts and agents call them
- every `--json` key and verdict/kind code: the agent contract
- any string that FLOWS INTO `--json` even if it reads like prose (a matcher's
  "why" reason, a verdict code also printed as a column tag). Trace a constant
  to its consumers before renaming; if it reaches JSON, leave it and list it
  for the reviewer as a later decision.
- on-disk folder names the tool creates (`_review/`, `_unknown/`), and example
  folder paths in docs that users type (`references/alice/`)
- HTML ids, `data-*` attributes, CSS classes, JS identifiers, bridge method
  names: renaming them is a logic change
- keyboard keys, code comments, docstrings, shipped step ids, dated logs
- doc headings that are link targets (`docs/cli.md#5-...`): renaming one
  silently breaks the anchor in another file

## Decisions to put to the reviewer, one line each

- a verb the glossary replaces but its "drop" list omits (e.g. "learn" when
  "teach" is the one verb): say whether every visible use goes
- a change to the CLI's human stdout (a banner): JSON is untouched, but user
  scripts grepping the old line break
- items of the review's "small changes" list that are really CSS/layout: name
  them and defer them, only their words change now
- glossary items that need a sliver of logic (a count in a button label, a
  new status like "strong" at a threshold): do them only if tiny, and flag each
  one separately in the report as "beyond words"

## Applying the edits

Use one helper for every file: a list of `(old, new[, expected_count])` pairs,
`assert text.count(old) == expected` (default 1) before replacing, write with
`newline=""`. The count assert catches a typo'd anchor and a phrase that also
occurs somewhere you did not mean to change. Keep the helper in the kernel and
re-define it if the kernel was reset (a NameError on the helper means it was).

## The guard test that keeps dropped words out

A plain grep of the source fails on identifiers (`rules-table`, `data-rule`,
`apply()`), so test only what the user sees:

- HTML: text nodes plus `title`, `placeholder`, `aria-label`, `alt`, via
  `html.parser` (stdlib).
- JS: string/template literals with the `${...}` parts removed. Do NOT filter
  by shape ("has a space or starts uppercase"): single lowercase words ARE
  shown (`el("span", "", "taught")`) and a shape filter hides them. Exclude
  instead: an explicit `CODE` set of known non-visible literals (event names,
  verdict prefixes like `"rule:"`), a kebab/snake identifier regex
  (`^[a-z][a-z0-9]*([_-][a-z0-9]+)+$`), and selectors (start `#`, `.`, `[`).
- Match `\b(word1|word2...)\b` case-insensitively; stems for verbs
  (`enrol\w*`, `learn\w*`).
- Parametrize per file so the failure names the file and the offending text.
- Prove it: put one old word back in a visible place (a button label), run
  only the guard file, watch it go RED naming that text, restore from a copy,
  confirm green and `git status` unchanged.

## Report

The size asked for (often 10 plain lines) plus before/after pairs of what a
user actually sees: one button, the counts line, a table cell, a CLI banner,
one page label. Separate lines for: what was left on purpose (JSON-bound
strings), what went beyond words, and the test/check counts.
