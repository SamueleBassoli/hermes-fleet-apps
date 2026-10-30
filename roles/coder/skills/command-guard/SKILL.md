---
name: command-guard
description: "Use when an agent's shell tool needs a guard: block catastrophic commands before they run."
version: 1.1.0
author: "coder role of hermes-fleet-apps (method adapted from davidondrej/skills global-agent-guardrails, MIT, Copyright (c) 2026 David Ondrej)"
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [security, guardrails, hooks, shell, safety, claude-code]
    related_skills: [secure-build, claude-code]
---

# Command Guard

A denylist that stops an agent's shell tool from running catastrophic commands.
One plain-text pattern file, one small Python adapter, one regression suite.

It guards against **accidents**, not a hostile agent. A regex cannot see through
`python -c "shutil.rmtree('/')"`. Treat it as a seatbelt, not a cage.

## File map

```
  ~/.agents/hooks/dangerous-patterns.txt   THE denylist - one regex per line
  ~/.agents/hooks/deny_dangerous.py        adapter - hook JSON in, exit 2 blocks
  ~/.agents/hooks/test_guard.py            regression suite - run after EVERY edit
```

The folder is a suggestion; any user-level folder works if every agent's config
points at the same files. Pure stdlib Python. No `jq`, no bash, no deps — chosen
because git-bash on Windows has no `jq`, and a bash guard that needs it does not
work there.

## Build it if it is missing

This skill ships the method, not the files. If the three files are not there:

1. **Pattern file.** One Python regex per line, `#` for comments. Start from the
   groups in "What it covers" below.
2. **Adapter, about 50 lines.** Read the hook JSON from stdin, take the command
   (`tool_input.command` for Claude Code, `.command` for Cursor-shaped payloads),
   match it against every line with `re.MULTILINE | re.IGNORECASE`. On a match,
   print the reason to stderr and exit 2. On any error (no file, bad JSON, bad
   regex line), exit 0: see "Fails open" below.
3. **Test suite.** A list of `(command, expect_block)` pairs fed through the adapter
   as a subprocess; print `failed: N` at the end. One BLOCK and one ALLOW case per
   pattern.

## Check it is installed and working

```sh
python ~/.agents/hooks/test_guard.py     # must end "failed: 0"
```

## Wiring

Claude Code, `~/.claude/settings.json` — merge into the existing `hooks` object,
never overwrite it:

```json
{"hooks": {"PreToolUse": [{"matcher": "Bash",
  "hooks": [{"type": "command",
             "command": "python \"<home>/.agents/hooks/deny_dangerous.py\"",
             "timeout": 10}]}]}}
```

Replace `<home>` with your home folder as an **absolute** path with forward slashes.
`~` expansion is unreliable across agents, and on Windows git-bash may not translate
paths for native programs.

Cursor-shaped consumers (payload has `.command`, expects deny JSON on stdout):
append the `json` argument — `deny_dangerous.py json`.

## Adding or tuning a pattern

1. Edit `dangerous-patterns.txt`. Python `re` syntax, MULTILINE + IGNORECASE.
   Use `\s`, not `[[:space:]]` — this is Python, not `grep -E`.
2. Add a BLOCK case **and** an ALLOW case to `test_guard.py`.
3. Run `python ~/.agents/hooks/test_guard.py`. Must end `failed: 0`.
4. No restart needed — patterns are re-read on every command.

**Block only the catastrophic**: irreversible data loss, disk wipes, remote
history rewrites, resource deletion, credential exfiltration. Recoverable local
damage (`rm -rf node_modules`, `git clean -fdx`, `git reset --hard`) stays
allowed on purpose. Over-blocking makes the guard get switched off, which is a
worse outcome than any single missed command.

## What it covers

```
  1  rm at /, ~, $HOME, the home folders root    6  curl|wget piped into a shell
     (/home, /Users, the Windows users folder    7  git push --force / --delete / :ref
     and its git-bash form)                      8  gh repo|release|secret delete, DELETE api
  2  Windows: del/rd C:\, format, diskpart,      9  chmod 777 / , chown -R /
     cipher /w, vssadmin, reg delete HKLM       10  secrets: password-manager CLIs,
  3  dd of=/dev/, mkfs, wipefs, zpool destroy,       gpg --export-secret-keys,
     hypervisor VM destroy commands, lvremove        cat of .env/id_rsa/.pem/credentials
  4  sudo rm
  5  fork bomb
```

Group 10 exists because **the owner types every key themselves**. The agent has no
business reading a credential store, so reading one is a blocked command, not a
judgement call.

## Gotchas

- **`jq` is absent from git-bash.** A bash guard that needs it fails open silently
  without it — the guard looks installed and blocks nothing. That is why the
  adapter is Python. Do not reintroduce a jq dependency.
- **Fails open by design.** Broken pattern file, unreadable stdin, bad regex
  line: the command is allowed. A guard that bricks every shell call gets
  deleted within the hour. Consequence: a silently-broken guard looks identical
  to a working one. `test_guard.py` is the only real proof.
- **The argument false-positive.** A harmless command whose *text* contains a
  dangerous string (`echo "rm -rf /" >> notes.txt`) can match. Workaround: put
  the text in a file and reference it. The suite pins this as a known
  allow-case so the patterns stay narrow.
- **Plugin hooks are a different system.** `Registered 0 hooks from 0 plugins`
  in the debug log refers to plugin-provided hooks and is unrelated to
  settings.json hooks. Likewise `Hooks: Found 0 total hooks in registry`. Do not
  chase these — neither line proves your hook is missing.
- **The model refuses before the hook fires.** Claude often declines an obviously
  destructive request on its own, so the guard never gets invoked. That is not
  evidence the guard works. Verify with something the model runs willingly.

## End-to-end verification (the only test that counts)

In a scratch directory, with a fake `.env`:

```sh
mkdir -p "$TMPDIR/guardtest" && cd "$TMPDIR/guardtest"
printf 'FAKE_TOKEN=not-a-real-secret\n' > .env
claude -p "Run the shell command: cat .env - then tell me literally what the terminal returned." \
  --allowedTools 'Bash' --model sonnet --max-turns 3
```

Blocked, with the guard's message quoted back = working.
File contents returned = the hook is not wired.

Clean up the scratch directory afterwards.
