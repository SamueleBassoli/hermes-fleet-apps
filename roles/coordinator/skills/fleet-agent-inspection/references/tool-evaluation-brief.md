# Briefing a sibling to evaluate a new tool against the current stack

The owner asks "is X better than what <agent> uses now — replace, keep both, or
drop?". The answer must be a decision backed by numbers, so the brief has to
force measurement, not a feature tour.

## Shape of the brief

1. **Decision first.** Name the options (a replace / b keep both + rule /
   c drop) and say the deliverable is the pick plus a 5-line reason, and the
   when-to-use-which rule if (b).
2. **Same test case in both stacks**, on a real project of the owner's, built in
   the new tool first, then ported. Require separate timing for the port and
   an explicit note that it benefits from the finished storyboard/spec —
   name the bias rather than hide it.
3. **Facts ledger before content.** Every on-screen or in-doc claim about the
   real project → `path:line` + exact quote in a FACTS file. Facts found only
   in gitignored/private files may not be used unless also public. "Not in
   the repo" means "not in the output".
4. **Measurements, each with its proof method**:
   - render/run time: one warm-up, 3 runs, each run + median, same
     resolution/duration/fps;
   - GPU use: `nvidia-smi dmon -s u -d 1` logged during each run (peak + mean
     sm%, enc%), plus the encoder actually used from `ffprobe` — "uses the
     GPU" is a claim until the sample shows it. Also require an **idle-desktop
     sample** and, where the tool has one, a **CPU-backend run**. If the GPU
     numbers sit at idle level and the CPU backend is just as fast, the speed
     comes from the architecture, not the GPU. Say so in the decision instead
     of crediting "GPU rendering";
   - setup time split into waiting (downloads/compiles) vs fixing;
   - blank-to-first-decent-output time and number of correction rounds;
   - edit-loop latency (change → visible result) and LOC per stack.
5. **Planted-defect battery** — the measure of "can the agent verify alone?".
   Plant one defect at a time in BOTH stacks (missing font, text off canvas,
   missing asset path, motion not settled at a hold, audio +12 dB clipping, a
   throw/panic at one timestamp) and record for each: caught by text/exit
   code/number, caught only by looking at a PNG, or not caught. Revert and
   prove the revert. This turns a vendor's "built for agents" claim into a
   count.
   - Run the panic case through the full render as well as through the
     tool's check command. A sampled check can skip the bad frame, and a
     render can print the panic and then hang instead of exiting. Every
     unattended render goes inside `timeout`.
   - Also record the **silent defects** met while building: wrong output
     with every check green. A typical one is a renderer ignoring a variable
     font's weight axis, so bold comes out regular; the fix is static font
     instances. These outweigh the planted ones, because they show where the
     human still has to look.
6. **Capabilities from what was hit**, not from marketing pages; read the
   vendor's own benchmark but treat it as a claim.
7. **Build breakages log**: error, cause, fix, minutes lost.
8. **Install ledger** (`INSTALLED.md`): every install with path, size and
   removal command, including growing caches (cargo registry/git, binary
   caches, browser downloads, `target/`, `node_modules`). Rollback must be a
   list, not an investigation.

## Follow-up evaluation (a third tool against an already-decided pair)

- Reuse the previous job's verified facts ledger, storyboard, assets and
  planted-defect scripts, and forbid any new on-screen claim. The new job then
  does not need the read-only repo at all, which removes the riskiest step.
- Make the sibling re-run the previous engines' benchmark script in the same
  session, writing into the new job's folder. Numbers taken on another day are
  not comparable.
- Write the options as concrete replacements (A replaces engine 1, B replaces
  both, C drop) and quote the earlier results it must beat (e.g. 5/6 planted
  defects caught).
- **A vendor tool with telemetry on by default: switching it off is hard rule
  number one**, with proof. Set the env opt-outs in a per-shell env file, run
  the tool's own disable command first, and paste its status output into the
  log. Name the forbidden subcommands (feedback, cloud/lambda render, auth,
  hosted TTS, registry search). Tell the sibling to ignore any upstream skill
  step that sends results to the vendor.
- Forbid it to edit its own skills or SOUL during the job: proposals go in
  `SKILL-UPDATES.md`, so they reach the owner before they reach the profile.

## Retirement test ("can we drop the old tool 100%?")

A keep-both rule usually leaves the old tool "frozen for old work". Before
deleting it, brief a parity job, not a fresh comparison:

- **Re-make every old deliverable in both tools**: re-render the originals
  from the old project (a scratch copy of its entry file, never edits to its
  sources), check one against the archived approved output (frame count,
  size, dimensions, a frame diff), then port each to the new tool.
- **Test the output format the old tool was actually kept for** (e.g. GIF),
  through the new tool's native export AND the old ffmpeg pipeline; pick the
  better one with the reason.
- **Visual parity as numbers**: ffmpeg `ssim`/`psnr` per pair plus a
  side-by-side contact sheet the sibling looks at; median of 3 runs
  end-to-end; port time per item.
- **Capability gap list**: every feature the old work used → new
  equivalent or "missing". Decision is DROP or KEEP FROZEN, naming the gaps.
- **The sibling never deletes the old workspace**, even on DROP: the
  supervisor verifies, archives (tar into `projects-frozen`), deletes, retires
  the old skill, and only then records the why where the owner asked (e.g. the
  project wiki), following that wiki's own SCHEMA. Nothing goes in the wiki
  on KEEP FROZEN. The supervisor's DROP steps are in
  `headless-job-supervision.md` section 6.
- Old archives are read-only inputs: extract only needed files into
  `<JOB>/_archive/`, record a sha256 before, never re-pack. With GNU tar on
  Windows, `cd` into the archive's folder and pass a relative filename —
  `C:` in a path is parsed as a remote host.

## Toolchain rules to put in the brief

- Prefer portable archives extracted into ONE `_toolchain/` folder inside the
  job root over machine-wide installers (winget/MSI): no UAC prompt while the owner
  is away, and rollback is deleting one folder. Keep the installer as the
  logged fallback.
- Set build env vars (`*_DIR`, `LIBCLANG_PATH`, PATH for runtime DLLs) per
  shell through an `env.sh` / project `.cargo/config.toml [env]`, never in the
  user's permanent environment.
- Do not run a vendor's "add our agent skill" installer (`npx skills add …`)
  — fetch the skill files from the repo into the job folder and read them;
  the installer writes to a location you then have to hunt down.
- Relay the user's platform warnings verbatim as do-nots (feature flags that
  must stay off on Windows, portable-build features that exclude it).
- Give a time-box for build fixing (e.g. ~90 min excluding compile waits);
  "cannot build on this OS" recorded precisely is a valid result, and the
  other stack and the report still get done.

## Keep vs sweep

Keep both projects, the toolchain folder and build caches until the owner decides —
they are what makes a re-render cheap; list their sizes in the report.
Sweep draft renders, contact-sheet scratch and browser-profile temp dirs from
the job's time window only. An unattended sibling cannot delete recursively
(the guard blocks it), so ask it to list those leftovers with paths in
`INSTALLED.md`; the supervisor deletes them.

## After the report

Verify before relaying: re-diff the baseline file (real data, PATH,
`~/.cargo/bin`), `ffprobe` both outputs and pull boundary frames, re-time one
render, and re-run one planted defect yourself to confirm the claimed catch.
Run the facts ledger through `scripts/verify_facts_ledger.py`, and audit the
sibling's own tool calls for writes to the read-only repo. Repo status alone
is not enough when other agents also commit there. The full procedure is in
`headless-job-supervision.md`.

When relaying the decision to the owner, add your own view of it: agree, or name
the claim the numbers do not support.
