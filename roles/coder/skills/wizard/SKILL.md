---
name: wizard
description: "Use when setup needs human hands. Builds a bash wizard."
version: 1.1.0
author: "coder role of hermes-fleet-apps (stage/library structure adapted from mattpocock/skills wizard, MIT, Copyright (c) 2026 Matt Pocock)"
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [setup, secrets, provisioning, bash, human-in-the-loop, migration]
    related_skills: [secure-build, build-method, setup-walkthrough]
---

# Wizard

A **wizard** is a throwaway bash script that walks the owner, step by step, through a
manual procedure the coder must not do itself. It opens each URL, says exactly what to
click and copy, captures the value with hidden input, writes it where it belongs, and
confirms before anything irreversible.

This is the mechanism that makes the security rule practical. The coder never reads,
echoes or types an API key. A wizard is how the owner types it themselves without the
coder having to re-explain the same dashboard walk every session.

## When to use

- Any credential, token, API key or password has to be created and pasted somewhere.
- A third-party dashboard must be clicked through (a DNS or CDN provider, a router admin
  page, a hypervisor UI, an OAuth app registration).
- A one-off migration or cutover with irreversible steps.
- A setup the owner will repeat on another machine (a second PC, a server, a fresh OS
  install).

**Don't use for steps the coder can perform itself.** If a CLI flag or config file does
the job, use that. A wizard for work the agent could have done is ceremony.

**Wizard or `setup-walkthrough`?** Both hand manual work to the owner; they differ in
artefact:

| | `setup-walkthrough` | `wizard` |
|---|---|---|
| Form | conversation, one step per reply | a bash script the owner runs |
| Best for | one-off, exploratory, the owner is already mid-screen | repeatable, many values, will be redone on another machine |
| Captures values | the owner edits the file themselves | the script captures and writes them |

When in doubt, walk them through it. Build a wizard when the same walk would otherwise
happen twice.

## Procedure

### 1. Scope the procedure

Read the repo before asking the owner anything cold:

- Setup: `.env`, `.env.example`, `README`, `docker-compose*`, framework config,
  `.github/workflows/*` (every `secrets.*` / `vars.*` reference is a value the wizard
  must produce).
- Migration: current state, target state, and the irreversible actions between them.

Show the owner the ordered stage list and the values each produces. They may add, drop,
reorder.

**Done when:** every stage is named in order, and for each captured value you know
(a) where the owner gets it, (b) where it is written (`.env`, a secret store, both, or
nowhere — some stages are pure actions), (c) whether it is secret (hidden entry).

### 2. Map each stage's journey

Write the precise path: which URL, what to click, where the value is shown, which
variable it fills. E.g. "Dashboard → Developers → API keys → Reveal test key → copy".

Where the current UI is unknown, **say so and check the docs or ask the owner**. Never
invent clicks that may not exist — a wizard that sends them to a page that no longer
exists is worse than no wizard.

**Done when:** every stage traces to concrete instructions a stranger could follow.

### 3. Author it

Copy `templates/wizard.sh` to the target path. Replace the example stage with one
`stage` per step, in dependency order. Set `TOTAL_STAGES` to match.

Helpers: `banner`, `stage`, `say`/`step`/`note`/`warn`, `open_url`, `ask`/`ask_secret`,
`write_env`, `set_secret`/`set_var`, `pause`/`confirm`, `finish`.

Hold the bar the template sets:

- `open_url` **before** asking for the value it produces.
- `ask_secret` for anything secret — never `ask`, which echoes to screen.
- `write_env` for every persisted value (it attempts chmod 600 — see Pitfalls).
- `confirm` before any irreversible action.
- One focused task per `stage` — each stage clears the screen, so anything the owner
  still needs must not have scrolled away.
- **Never hand-edit the library above the STAGES marker.** That consistency is the point.

### 4. Verify and hand off

```bash
bash -n path/to/wizard.sh            # syntax
shellcheck path/to/wizard.sh         # if available
chmod +x path/to/wizard.sh
```

Do **not** run it end to end yourself — it opens browsers and blocks on human input,
and running it would put the coder in the path of a secret. Trace it statically instead:
every value from step 1 is captured and lands where step 1 said it would.

Tell the owner the exact command to run it. Ephemeral by default: delete it when the job
is done, and say so in your report. Commit it only when the owner wants a repeatable
setup path in the repo.

## Pitfalls

- **Echoing a secret back for confirmation.** Never print a captured secret, not even
  masked, not even "first 4 characters". Confirm by testing the credential works, not by
  showing it.
- **Forgetting `.gitignore`.** A wizard that writes `.env` into a git repo with no
  ignore rule has just staged the owner's key. The template warns; do not suppress the
  warning.
- **Running the wizard to "test" it.** Static trace only. The whole point is that the
  coder is not in the room when the key is typed.
- **Windows/git-bash.** `open_url` falls through to `explorer.exe`, which works from
  git-bash. `read -rs` works. `tput` may report no colours in some terminals — the
  template degrades to plain text, which is fine.
- **`chmod 600` is a no-op on Windows.** Verified: on an MSYS/git-bash mount the file
  stays `-rw-r--r--`. The call is kept because it is real on Linux and macOS. On
  Windows, do NOT tell the owner the file is locked down — the `.gitignore` guard is the
  protection that actually holds there. If a Windows `.env` genuinely needs locking,
  that is `icacls`, and the owner runs it themselves.
- **Wizard for agent work.** If every stage is something the coder could run, delete the
  wizard and just run it.

## Attribution

Stage/library structure adapted from Matt Pocock's `wizard` skill
(github.com/mattpocock/skills, MIT). Security hardening (600 perms, no-echo rule,
no-self-run rule, gitignore guard) is this fleet's own.
