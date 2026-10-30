# Steering Layers — paths, formats, budgets

Reference for the five places a durable instruction can live in a Hermes
profile. Load when you need exact paths, file formats, or the ownership rules
for a specific layer.

## Resolving the profile home

All paths below are relative to the ACTIVE profile home. Resolve it from
`$HERMES_HOME`; do not hardcode the default install path. A named profile lives
at `<hermes home>/profiles/<name>/` and has the same directory layout as the
default install, which is exactly why habit-built paths write to the wrong
agent without erroring.

A profile's `skills/`, `cron/`, `memories/`, and `plugins/` belong to that
profile alone. The default install's copies are a different agent run from a
different shell — leave them alone unless explicitly directed otherwise.

## SOUL.md

`<profile>/SOUL.md`

Plain markdown prose, injected verbatim into the system prompt every turn. No
frontmatter, no schema, no size enforcement — but it is paid for on every turn,
so length is a real cost.

Hand-editable. Back up to `<profile>/backups/` before rewriting.

Ships with stock text that names the agent generically. A profile still
carrying the stock wording has never been personalized, regardless of what else
in the profile is populated.

Belongs here: voice and reply length, autonomy level, candour/pushback,
honesty about unverified results, where corrections get routed.

Does not belong here: facts about the user or environment. They cannot be
updated by the memory tool from a later session and will go stale silently.

## Memory stores

`<profile>/memories/USER.md` — who the user is.
`<profile>/memories/MEMORY.md` — agent notes: environment, conventions, quirks.

Uppercase filenames, inside `memories/`. Both are injected every turn and both
are character-capped; the memory tool reports usage as a percentage on write.

**Tool-managed — do not hand-edit.** Entries are separated by a `§` record
marker and the budget is enforced at write time. Hand edits bypass both. The
`.lock` files alongside them are runtime artifacts, not content.

The memory tool only ever writes to the **active** profile. To seed a profile
you just created, hand-write both files there — that is the one correct use of
a hand edit, and only before that agent has run for the first time.

Write entries as declarative facts, not imperatives: "User prefers concise
replies" rather than "Always reply concisely" — imperative phrasing is re-read
in a later session as a live directive and can override that session's actual
request.

When the store is full, the add is rejected with current entries shown. Reissue
as ONE batch that removes or shortens stale entries and adds the new one
together — the cap is checked only against the final state of the batch, so a
single call can consolidate and add even when the add alone would overflow.

## Skills

`<profile>/skills/<category>/<name>/SKILL.md`

Loaded on demand when the description matches the task, so depth here is
cheap in a way that SOUL and memory depth is not. This is the layer that holds
"how to do X for this user."

The description is budgeted to roughly 60 characters and is truncated in the
index beyond that, which destroys the routing signal. Write it trigger-first as
one short sentence and put every bit of detail in the body. `skill_manage`
refuses a create outright when the description is too long; writing the
`SKILL.md` file directly bypasses that check, so apply the cap by hand when
seeding skills into another profile.

Each `<category>/` directory takes a `DESCRIPTION.md` holding a single
`description:` frontmatter line. Without it the category appears unlabelled in
the index and the agent has no signal for what the group contains.

Ownership matters for writes: bundled, hub-installed, pinned, and user-owned
skills refuse autonomous edits. A bundled skill being the most relevant one
does not make it writable — create or extend a curator-managed skill instead.

## Measuring what a layer costs

```bash
hermes -p <name> prompt-size          # per-turn cost, offline, no API call
hermes -p <name> prompt-size --json   # machine-readable
```

It breaks the system prompt into stable (identity, guidance, skill index),
context (AGENTS.md, cwd files), and volatile (memory, user profile, timestamp)
tiers, then lists every toolset and every skill by size. Run it before and
after any identity change so the delta is visible — a SOUL rewrite and a skill
purge move very different numbers, and guessing which one mattered wastes the
next trim.

## Project context files

`AGENTS.md` (also `.hermes.md`, `CLAUDE.md`) in a repository root.

Scoped to that codebase, loaded when working there. Rules that only make sense
inside one project go here rather than in memory, which has no scoping
mechanism and would fire the rule during unrelated work.

The same filenames also work at the **user level** — `~/.claude/CLAUDE.md` is
read by Claude Code on every session in that home directory. That is the only
documentation layer a non-Hermes CLI agent reads: it shares nothing with a
Hermes profile's SOUL, memory, or skills. When a convention must reach every
agent the user runs, this file is the delivery mechanism for the ones outside
Hermes, and it must be written once per OS home the user works in (a Windows
home and a WSL home are separate). Copying it across that boundary needs
`sed -i 's/\r$//'` — CRLF line endings break shell parsing on the Linux side.

## Enforcement vs documentation

Every layer on this page is documentation: it steers an actor that loads it.
None of them constrain the user at a shell, a cron job, or a CLI agent that
never read them.

For a rule whose violation is expensive or irreversible, pair the docs with a
gate the tool enforces itself. For git identity and content rules that is a
global hook directory:

```bash
mkdir -p ~/.config/git-identity-hooks
# write pre-commit, then:
chmod +x ~/.config/git-identity-hooks/pre-commit
git config --global core.hooksPath ~/.config/git-identity-hooks
```

`core.hooksPath` applies to every repository on that machine, including ones
cloned or created afterwards, for every actor — which per-repo `.git/hooks`
cannot do, since it is not cloned and not shared. Install it once per OS, and
make the refusal message state the corrective command so an actor that never
read the docs can still fix itself.

Prove a gate with both a passing and a failing commit. An unreachable or
non-executable hook is silently skipped and looks exactly like a working one.

## Choosing a layer

Ask two questions in order:

1. **Is it true in every session regardless of task?** If no, it is a skill (or
   an AGENTS.md rule if it is repo-scoped). If yes, continue.
2. **Is it a fact or a behaviour?** Fact about the user → memory `user`. Fact
   about the environment → memory `memory`. Behaviour or voice → SOUL.md.

A rule that starts with "when doing X…" fails question 1 by construction and
belongs in a skill, no matter how strongly the user stated it.
