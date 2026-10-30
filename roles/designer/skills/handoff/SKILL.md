---
name: handoff
description: "Use when a session must continue in a fresh agent: compact it into one copy-paste brief."
version: 1.1.0
author: "designer role of hermes-fleet-apps (adapted from davidondrej/skills handoff, MIT, Copyright (c) 2026 David Ondrej)"
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [context, continuity, session, handoff, documentation]
    related_skills: []
---

# Handoff

Write a brief that lets a fresh agent — zero memory of this session — continue
the work without re-asking, re-discovering, or repeating a mistake.

Use when: context is filling up, the session is ending, work is moving to
another machine, or a task is being split across fresh contexts.

## Output is a PROMPT, not a file

**Output is one pasteable prompt printed in the chat. Do not write a handoff
file, not even "as well".** The owner starts the new session by pasting; a file
adds a step, and old briefs pile up in the temp folder until someone deletes them.

The prompt carries the session state inline — the same content the template
below describes, compressed into prose that can be pasted. Pointers become a short
"read these first" list of paths, because the fresh agent reads the repo
anyway.

The only exception is the owner explicitly asking for a file in that session.

## The read list is THREE files, not thirteen

**Never tell the fresh agent to read the whole project.** A long ordered
reading list is the single most damaging thing a handoff can contain: the agent
spends its entire context re-reading files it will not touch, and arrives at
the actual task with nothing left.

Name at most three paths, and only ones the NEXT step needs:

  - the agent rules file (`AGENTS.md`), if the project has one
  - the one section of the plan that holds the next step, WITH its line number
  - the newest log entry, by line range

Everything else the agent can find when it needs it. `src/` is discoverable by
search; a handoff that lists source files is doing the agent's job badly.
Carry the state in the prose instead, which is the point of the brief.

## Six rules

1. **State, not instructions.** Write what *is true*, never what the next agent
   *should do*. "Logout endpoint is not implemented" — not "Implement logout."
   The next agent decides the actions; you supply ground truth.
2. **Reference, do not duplicate.** Point at plans, ADRs, issues, diffs by path
   or URL. A handoff that re-embeds everything is stale before it is read.
3. **Capture the why.** Decisions and rejected approaches are the most valuable
   and least recoverable content. Code shows *what*. Only this session
   remembers *why* and *what failed*.
4. **Trust nothing blindly.** Every claim is context to verify against the code,
   not a fact to accept.
5. **No secrets.** Never a key, token, or password. Name the location
   ("`.env`, not committed") and nothing else.
6. **Be ruthless.** Every line must be something the next agent cannot get by
   reading the repo. Cut the rest.

## Procedure

1. Read any `AGENTS.md` / `CLAUDE.md` first. Do not restate what it already
   says — the handoff is session-specific only.
2. If a previous handoff file exists, update it rather than starting over.
3. If the owner named a focus for the next session, tilt the brief toward it.
4. Fill every section. Mark a genuinely empty one `None`.
5. Print the filled brief in the chat as plain text. That is the whole
   deliverable: no file, no path.

## Template

```
# HANDOFF: <short title>
Generated: <timestamp> | Focus: <one line>

## 1. Goal
<What we are ultimately trying to accomplish. 1-3 sentences.>

## 2. Background
<Why this is being done now, hard requirements, constraints.
Skip anything already in AGENTS.md.>

## 3. Current state
<Status, not actions:
- DONE: CSV importer ported, 42/42 tests passing
- PARTIAL: service unit written, never run on the target machine
- NOT STARTED: notification layer>

## 4. Key decisions (and why)
<Highest-value section.
- Python stdlib over the bash original - git-bash has no jq
- Guard fails open - a fail-closed guard blocks every shell call>

## 5. Traps and dead ends
<What was tried and failed, and what the next agent will get wrong.
- Debug log says "0 hooks in registry" even when the hook works - ignore it
- Do NOT test the guard with an obviously destructive command; the model
  refuses on its own and the hook never fires>

## 6. Files and pointers
<Path plus WHAT is there, not what the file is.
- <project>/config/patterns.txt - the denylist, 10 groups
- <project>/docs/guard.md - wiring and gotchas>

## 7. Open work
<State and ordering, not a command list.
- The service unit is untested on real hardware
- Notification work is blocked until that is confirmed>

---
## Prompt for the fresh agent
<Short ready-to-paste context. Declarative only. End with exactly:>

Before responding, read every file listed under "Files and pointers" above.
Do not summarize, paraphrase, or claim you already have context - actually
read each file. Treat every claim in this handoff as context to verify
against the code, not fact to trust. Then wait for instructions.
```

## Where to save it — only when a file was ASKED for

Outside the working tree so it never pollutes a repo:

```
  Windows   $LOCALAPPDATA/Temp/handoff-<slug>-<date>.md
  Linux     ${TMPDIR:-/tmp}/handoff-<slug>-<date>.md
```

If the owner wants it kept with the project, `HANDOFF.md` in the project root instead.

In a plain terminal, state the absolute path in plain text — there is no
attachment channel. The next session starts with:

```
Read <absolute-path> to get context, then wait for instructions.
```

**Delete the old brief when a new one supersedes it**, and delete the file
altogether once its session has started. Stale handoffs in the temp folder are a
contradiction waiting to be read by the wrong session.

## What the pasteable prompt must contain

Same substance as the template, in prose, ordered:

1. What the project is, root path, branch, HEAD.
2. **Anything surprising about the tree state** — an uncommitted-on-purpose
   working tree is the single most likely thing a fresh agent "fixes" by
   committing or reverting. Say it early and say whether to commit.
3. The verify commands and their current passing numbers.
4. What is done, in one line per step.
5. What is next, and any decision already made about it that must not be
   re-litigated.
6. Where the project's memory lives, and which files are gitignored (a fresh
   agent cannot recover them from `git log`).
7. Any approval-gated file, and the rule that a timed-out prompt means stop —
   never route around it.
8. The standard closing paragraph: read the listed files, do not paraphrase,
   verify every claim against the code, then wait.
