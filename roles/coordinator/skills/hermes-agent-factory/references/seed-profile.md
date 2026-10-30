# The Seed Profile

`seed` is a profile that exists **only to be cloned**. Never chat with it,
never give it memories, never let it accumulate sessions. It is a stencil.

Why it exists: creating from scratch means re-deciding the same things
every time and forgetting one. Cloning a seed makes a new lean agent a
single command.

## What belongs in it

| in | out |
|---|---|
| model + provider defaults | memories (`USER.md`, `MEMORY.md`) |
| minimal `platform_toolsets` | sessions / chat history |
| skeleton `SOUL.md` with placeholders | messaging channel config |
| genuinely universal skills | cron jobs |
| | project-specific anything |

## Building it

```bash
# 1. create it empty
hermes profile create seed --description "Template profile. Clone source for new agents. Not for direct use."

# 2. model defaults
hermes -p seed config set model.default <model>
hermes -p seed config set model.provider <provider>

# 3. minimal toolsets — the important part
hermes -p seed config set platform_toolsets.cli '[terminal, file]'

# 4. write the SOUL skeleton (see below)

# 5. confirm it is lean
hermes -p seed prompt-size
```

Do not put API keys in the seed's `.env` unless every future clone should
inherit them. Cloning copies `.env` verbatim. A seed carrying every key
you own means every agent you ever spawn carries every key you own.

That is the seed's one real hazard. Decide deliberately: an empty seed
`.env` means the user adds keys per agent (safer, more typing); a
populated one means instant clones with a wide blast radius.

## SOUL skeleton

Write to `$HERMES_HOME/profiles/seed/SOUL.md`. Placeholders are literal —
they must be replaced in every clone.

```markdown
You are <NAME>, a Hermes agent serving <OWNER>.

IDENTITY
<NAME> is the agent that <ONE JOB> on <WHICH MACHINE>.
In scope: <WHAT IT HANDLES>
Out of scope: <WHAT IT REFUSES AND HANDS BACK>

VOICE
Short. Bullet points over paragraphs. Plain words, no jargon.
No filler, no restating the request. On a long job: one line at the start, then
speak again only when the plan changes.
A finished job gets: what changed, what is verified, what is left.

LIMITS
Never <DANGER 1>.
Never <DANGER 2>.
Never read, copy, or move credentials. Point <OWNER> at the file and stop.
Install nothing unless the job requires it.
When unsure whether an action is destructive, stop and ask.

REPORTING
The deliverable is a working artifact backed by real tool output, never a
description of one. If something fails or cannot be verified, say so.
A reported blocker beats an invented result.
After every job, remove scratch files and temp artifacts, and say what was removed.
```

## Cloning from it

```bash
hermes profile create <name> --clone-from seed --description "<role>"
```

Then immediately:

1. Overwrite `SOUL.md` — replace **every** placeholder.
2. Adjust `platform_toolsets` for the role.
3. Add role skills.
4. Hand `.env` to the user for keys.
5. `hermes -p <name> prompt-size` and record it.

A clone still containing `<NAME>` or `<ONE JOB>` is unfinished. Grep for
it before declaring done:

```bash
grep -n '<[A-Z ]*>' "$HERMES_HOME/profiles/<name>/SOUL.md"
```

## Maintaining the seed

When a lesson turns out to apply to *every* future agent, fix the seed —
not just the agent you are working on. That is what makes the factory
improve instead of repeating mistakes.

Changes to the seed do **not** propagate to existing clones. A clone is a
copy, not a link. To push a change everywhere, edit each profile or
rebuild them.

If you need real propagating updates, use a **profile distribution**
(a git repo installed with `hermes profile install`, updated with
`hermes profile update`) instead of clone-from-seed.
