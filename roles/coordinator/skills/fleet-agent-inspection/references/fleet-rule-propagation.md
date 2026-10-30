# Propagating a standing rule across the fleet

When a convention changes — identity mapping, project layout, publishing rules,
naming — every agent that touches the affected projects needs it, and each one
reads a different channel.

| Who | Channel |
|---|---|
| other Hermes profiles | a skill in **their** profile, plus one line in their `MEMORY.md` pointing at it |
| Claude Code | `~/.claude/CLAUDE.md` — it does not read Hermes skills |
| anyone, including scripts | a machine-enforced guard (e.g. a global git hook) |

## Rules

- A skill written into another profile **without YAML `name`/`description`
  frontmatter is never loaded**: the file looks right and is inert.
- Home directories differ per environment: on a machine with WSL, `~/.claude/`
  and `~/.config/` exist twice and both need the file.
- Instructions can be ignored; a guard cannot. When the rule matters, ship the
  guard as well as the document — recipe, tests and WSL notes in
  `machine-enforced-guards.md`.
- **Every later change to the convention must re-reach every channel.** Moving
  one project between identities invalidates the map in the rules file, in each
  sibling's skill, in every `CLAUDE.md` and possibly in the guard. Propagating
  to three channels and forgetting the fourth is worse than not propagating at
  all: one agent then works from a map that looks authoritative and is wrong.
  Keep the channel list above and walk it end to end each time.
- **Name each channel's file by what it governs, not by the session.** The
  propagated skill is `publishing-identity`, not `identity-fix-<date>`;
  the sibling reloads it for months.
- **Editing a sibling's profile needs the owner's say-so.** Propagation is the one
  standing exception, and only for rules that directly govern the projects that
  agent works on — never its unrelated skills, memories, config or crons.
