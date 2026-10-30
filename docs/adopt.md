# Adopt the fleet

Step by step, for someone who already uses Hermes Agent. You need Hermes installed and one
model provider working. Which model and provider you use is your choice.

The commands below match `hermes --help` and `hermes profile --help`. If your Hermes version
differs, check `--help` first.

## 1. Create one profile per role

Profile names are lowercase letters and digits. Use the role names: the briefs and skills
refer to the roles by these names.

```
hermes profile create coordinator
hermes profile create coder
hermes profile create qa --no-skills
hermes profile create product --no-skills
hermes profile create designer --no-skills
hermes profile create media --no-skills
hermes profile create docs --no-skills
```

- `--no-skills` leaves out the bundled Hermes skills (it writes a `.no-bundled-skills` file
  in the profile). The coordinator and the coder keep the bundled skills; the other five load
  only their own, as their `SOUL.md` says.
- Give each profile a one-line description, so the kanban board can route by role:
  `hermes profile describe <role> --text "..."`. The table in the README has one per role.
- `hermes profile create` prints the profile folder. You can also see it later with
  `hermes profile show <role>`.

## 2. Copy the role files in

For each role:

- copy `roles/<role>/SOUL.md` into the profile folder, replacing any `SOUL.md` there;
- copy every folder in `roles/<role>/skills/` into the profile's `skills/` folder.

Hermes finds a skill by its `SKILL.md`, at any depth under `skills/`.

## 3. Install the third-party skills

[third-party-skills.md](third-party-skills.md) lists, per role, the skills other people
wrote. Each `SOUL.md` names them at the step where they apply, so install them into the
role that uses them:

```
hermes -p <role> skills install <install id>
```

A row that links to a GitHub repo instead of an install id: follow that repo's own install
steps.

## 4. Set the config values that matter

Open each profile's config with `hermes -p <role> config edit` and set:

```yaml
agent:
  max_turns: 150            # tool iterations per run
compression:
  threshold_tokens: 150000  # compress the context at about 150k tokens
```

Set the reasoning effort from a chat with the role: run `hermes -p <role> chat` and type
`/reasoning xhigh --global` (coordinator: `/reasoning medium --global`). `--global` saves
the level in that profile's config, so every later run uses it.

Why these values:

- **Compression at about 150k tokens.** Every role counts compressions: after the second one
  in a job it writes a handoff and stops. If your model's context window is small, Hermes
  compresses earlier (`compression.threshold` is a share of the window, and the lower of the
  two wins).
- **150 iterations per run.** Enough for one leg of work, about three deliverables. The
  coordinator splits bigger jobs into legs.
- **Reasoning effort.** The coordinator routes and talks to you all day: `medium` keeps it
  quick. Product, designer, coder, qa, media and docs do the heavy thinking: `xhigh`.

Pick each role's model with `hermes -p <role> model`.

## 5. Start small, then grow

1. **coordinator + coder.** Give the coordinator a small idea. It writes the brief and hands
   the build to the coder.
2. **Add qa.** From now on the builder no longer grades its own work.
3. **Add product and designer.** Now the two gates exist: you approve the spec, then the
   design.
4. **Add media and docs** when a project gets close to a release.

Every `SOUL.md` mentions the fleet map, `FLEET.md`: who does what, in one or two lines per
role. Ask the coordinator to write it from the README's role table, keep it where every
profile can read it, and update it when you add a role.

## 6. Kanban: how the coordinator chains the work

The coordinator's skill `fleet-project-pipeline` holds the full method. In short:

- Every job is one kanban card, assigned to one role. The brief is committed in the project
  repo first (`jobs/JOB-<nnn>-<role>-<topic>/BRIEF.md`); the card body points at it.
- Stages are chained with `--parent`: a card waits until its parent is done, then starts by
  itself. A card with no parent starts at once, in parallel with the others.
- A worker finishes with `kanban_complete` and a `REPORT.md` next to the brief. It never
  creates cards: follow-ups go in the report, and the coordinator plans them.
- After each card the coordinator reads the report and the result, checks the commit, and
  merges only when the tests pass.
- A qa FAIL becomes two chained cards: a coder fix, then a qa recheck.
- Keep the board's review lane manual, so no agent approves its own work past your gate.
- `scripts/kanban-card.sh` in that skill creates a card and, when you set
  `KANBAN_NOTIFY_PLATFORM` and `KANBAN_CHAT_ID`, subscribes your chat to it.

See `hermes kanban --help` for the board itself.
