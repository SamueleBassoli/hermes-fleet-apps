# Community-ready design

What changes when the user of a tool is a stranger on unknown hardware instead of the
author on their own machine. Decide this at shape time, because it constrains the stack, not the
polish.

## The rule

Do not build for the machine in front of you when the stated audience is a community.
The development machine's GPU, drive layout, and installed toolchain are accidents of
whose desk it sits on.

## Dependencies are support requests

Every dependency is a future issue filed by someone whose environment you cannot see and
cannot debug. Fewer, older, more boring dependencies win.

- Prefer a standard library over a package, and one package over a stack.
- Reject anything that requires a running server process for data volumes that fit in
  memory. A server is a second thing the stranger must install, start, and keep alive.
- Check that a chosen package publishes working wheels for Windows, Linux and macOS, on
  both Intel/AMD and Apple Silicon, before committing to it. A package that compiles
  from source on install is a package that fails on someone's laptop.

## Target the common denominator, make the fast path a setting

Build and test against plain CPU and no accelerator. GPU support fragments immediately
by vendor and operating system, and each branch needs hardware to test on.

Keep hardware selection as a **single config value** consumed by one line of code, never
a separate code path. Then accelerated execution is a setting someone flips, not a port
someone maintains. Say this explicitly rather than promising GPU support on a roadmap:
an unfulfilled roadmap item is a support burden with no code behind it.

## Interfaces, in order

```
  engine (library/CLI)  ──▶  local web UI  ──▶  agent / messaging
  all behaviour lives here    only where visual      just another caller
                              judgement is needed
```

- The CLI is the engine: scriptable, testable, callable by anything, no UI dependencies.
- Add a GUI only where the task genuinely needs eyes — choosing between images, judging a
  diff, confirming a destructive batch. Asking a visual question in a terminal forces the
  user to open files by hand, which makes the whole flow useless.
- Prefer a small local web page served from the tool over a native desktop toolkit: one
  implementation works identically on every OS with nothing extra installed.
- An agent or chat integration is **not a second product**. It calls the same commands a
  human calls and gets no special powers. Two front-ends over one engine; two engines is
  two sets of bugs.
- The same requirement therefore produces one command, reachable three ways — design the
  command first and let each surface be a thin caller.

## Machine-readable output

If an agent or script will ever drive the tool, give every command a `--json` flag that
prints the same result as a structured object. Same code path, one flag. Parsing human
output is the thing that breaks on every cosmetic change.

## Reversibility is a feature, not a safeguard

A tool that moves, renames, or deletes the user's files ships its undo in the same
release as the operation — a run journal recording source and destination per file, and
a command that replays it backwards. Strangers will point it at the wrong folder. Make
that a thirty-second annoyance rather than a data-loss report.

Default to the non-destructive mode where it costs nothing, and make destructive modes
explicit flags that print a dry-run plan first.
