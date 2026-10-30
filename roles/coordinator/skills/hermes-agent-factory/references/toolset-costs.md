# Toolset Costs

Measured with `hermes prompt-size` on a full default CLI profile
(25 tools, ~40.4 KB of tool schema). Sizes drift between versions —
**re-measure, do not trust this table as gospel.** It is for ranking,
not for arithmetic.

## Measured sizes (largest first)

| toolset | tools | schema | keep it when |
|---|---|---|---|
| `file` | 4 | 5.4 KB | the agent reads or writes files (usually yes) |
| `browser` | 5 | 4.4 KB | it drives a real browser |
| `delegation` | 1 | 4.0 KB | it is an orchestrator spawning subagents |
| `skills` | 3 | 3.6 KB | it should load or write its own procedures |
| `browser-use` | 1 | 3.5 KB | paired with `browser` — same use case |
| `terminal` | 1 | 3.4 KB | it runs commands (usually yes) |
| `memory` | 1 | 3.3 KB | it should remember across sessions |
| `code_execution` | 1 | 3.0 KB | it needs multi-step scripted logic |
| `web` | 2 | 1.9 KB | it searches or fetches pages |
| `tts` | 1 | 1.9 KB | it speaks out loud |
| `clarify` | 1 | 1.6 KB | a human is present to answer |
| `vision` | 1 | 0.8 KB | it looks at images |

Other toolsets exist (`cronjob`, `todo`, `image_gen`, `computer_use`,
`connections`, `session_search`, `stt`, `video`, `x_search`,
`homeassistant`, `discord`, `spotify`, ...). List what a profile actually
has with `hermes -p <name> prompt-size`.

## The main lesson

On a default profile: **tool schemas ~40 KB vs identity+skills ~9 KB.**

Tools are roughly four times the cost of everything else. Trimming
toolsets is the highest-leverage anti-bloat action available. Shortening
SOUL.md is nearly pointless by comparison — optimise tools first.

## Role presets

Starting points, not laws. Add only on evidence the role needs it.

**Headless worker** — does one job on a schedule, no human present
```
[terminal, file]
```
No `clarify` (nobody to ask), no `tts`, no `vision`, no `browser`.
Add `memory` only if it must learn across runs.

**Researcher** — reads, searches, writes findings
```
[web, file, memory, code_execution]
```
Add `browser` + `browser-use` only for sites that need real rendering;
`web` alone handles most fetching at a fraction of the cost.

**Coder / builder** — edits code on a machine
```
[terminal, file, code_execution, skills, memory]
```

**Orchestrator** — decomposes work and spawns others
```
[delegation, terminal, file, skills, memory, todo]
```
The only role where `delegation` earns its 4 KB.

**Daily driver** — a human's main agent
Everything the human actually uses. Bloat is acceptable here because
breadth *is* the job. Do not apply worker presets to a daily driver.

## Per-platform lists

`platform_toolsets` is keyed by platform (`cli`, `telegram`, `discord`, ...).
Only populate the platforms the agent actually runs on — an unused
platform block is dead config, and an agent reachable on a platform you
forgot about is a security problem, not just bloat.

```bash
hermes -p <name> config set platform_toolsets.cli '[terminal, file]'
```

## Re-measuring

```bash
hermes -p <name> prompt-size                  # human readable
hermes -p <name> prompt-size --json           # parseable
hermes -p <name> prompt-size --platform telegram
```

Runs offline. No API call, no cost. Run it freely — before and after
every trim, so the delta is visible.
