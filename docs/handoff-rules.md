# Handoff rules

Who leaves what for whom. Every handoff is a file in the project's git repo, never a chat
message and never an agent's memory: the next role reads the repo.

## The chain

```
idea -> product   -> SPEC.md, tickets/                       gate: you approve the spec
     -> designer  -> .design/ (brand.md, ui-plan.md, tokens.json,
                     logo/, imagery-briefs.md, research.md)  gate: you approve the design
     -> coder     -> code + tests + CHANGELOG entry
     -> qa        -> QA-REPORT.md (pass/fail, punch-list)
     -> media     -> assets/ (gif, mp4)
     -> docs      -> README, store listing, release notes
```

## Role by role

**coordinator**
- Gets: your ideas, and every role's report.
- Leaves: one brief per job (`jobs/JOB-<nnn>-<role>-<topic>/BRIEF.md`) with a kanban card
  pointing at it; a short report to you when a stage ends.
- Keeps: the fleet map (`FLEET.md`, who does what) and the project's checklist (which stage,
  which gate).

**product**
- Gets: your idea.
- Leaves: `SPEC.md` (goal, users, in and out of v1, screens, data sources, acceptance
  criteria a tester can run, open questions) and `tickets/` (small, ordered, one idea each).
- For: the designer and the coder. A spec you have not approved is a draft.

**designer**
- Gets: `SPEC.md`.
- Leaves: `.design/`, with every value the coder needs named in a file. No "TBD".
- For: the coder, who builds without asking a design question; media, who takes every
  colour, font and duration from `tokens.json`. A direction you have not approved is not final.

**coder**
- Gets: `SPEC.md` and `.design/`.
- Leaves: code, tests, a CHANGELOG entry, a branch or pull request.
- For: qa. Its own checks are never the final word.

**qa**
- Gets: a build or a pull request.
- Leaves: `QA-REPORT.md`: verdict PASS / FAIL / BLOCKED, pass or fail per acceptance
  criterion, a punch-list by severity with reproduction steps, and what was not tested and why.
- For: the coder (who fixes) and the coordinator (who merges, or sends a fix and a recheck).
  qa never edits project files.

**media**
- Gets: `.design/` and a working build.
- Leaves: `assets/` (gif, mp4). Every render is looked at before it is reported: text inside
  the safe area, nothing clipped, colours matching `tokens.json`.
- No `tokens.json` means the project is not ready for motion: media stops and says so.
  It never publishes; it hands you the file path.

**docs**
- Gets: a qa-passed build and `.design/`. No PASS, no release.
- Leaves: README, CHANGELOG, release notes, store listing.
- For: you. Nothing goes public without your go for that action.

## Rules for every handoff

- Every job ends with a report: the files it wrote, by path; what is verified; what is left;
  which scratch files it removed.
- Work outside a role's scope is handed back in one line, naming the right role.
- Workers do not create kanban cards. Follow-ups go in their report; the coordinator plans them.
- After the second context compression in one job, the agent writes a handoff (skill
  `handoff`): one copy-paste brief, so a fresh session continues from the files.
- Knowledge that outlives one session goes in the repo's `wiki/`, one per project.
- Credentials never travel in a handoff. The role names the file and the variable; you fill
  it in.
