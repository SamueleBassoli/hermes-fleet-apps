# Local-AI desktop app: SPEC shape

For an app that runs a local model (image, LLM, voice) for a non-technical user on their
own GPU.

## Engine
- Wrap an existing runtime (e.g. llama.cpp or stable-diffusion.cpp) as a subprocess per
  job, pinned to one tested release (version + sha256 in code). It updates only when the
  app updates, so an upstream change cannot break it silently.
- GPU on demand: the engine runs only while a job runs; nothing resident when idle. One
  job at a time, a queue, and a Cancel that kills the process.
- Calibrate with the SAME flags the app passes: a spike measured with a speed flag the
  app omits (memory-mapped loading, for example) hides a several-times slowdown until the
  live run.
- Stream the engine log to disk line by line (not written at exit): a 0-byte log during
  a 5-minute job cannot be diagnosed.
- Give the app an engine-path override env var (`<APP>_ENGINE`): when a live run finds a
  missing flag, you can keep testing with the override while the coder fix runs. Once the
  fix is merged, time one job from the real UI WITHOUT the override: the override proves
  nothing about the shipped code.
- Let the runtime place weights GPU → RAM → disk with its own flags. The app predicts and
  labels; it does not reimplement placement.
- Self-contained: the app downloads its own engine + models into its data folder and
  never reads other projects' files. Offer a user-triggered "import models from a folder"
  (same size/hash check, source untouched) so a PC that already has the files skips the
  download.
- Every user-facing control whose effect is not obvious gets a one-line hint next to it,
  and its useful range is measured in the live end-to-end test (pixel diff, timing), not
  judged by eye.

## Catalogue
- Build it from `https://huggingface.co/api/models/<repo>/tree/main?recursive=true` (exact
  names + byte sizes), pin it in a file, verify every download by size (and sha256 when
  published). Resumable `.part` downloads.
- Third-party quantised files are CANDIDATES until the spike proves each one loads in the
  pinned runtime and records its recommended settings; drop any that fail.
- "Recommended" = the highest-quality option that fits fully on the GPU; if none, the
  fastest that runs.
- Answering "is there variant X?": read the repo tree sizes from the API, never the repo
  name. A model's file size tells you what it is.
- Do not ship a tier you cannot test on real hardware: park it as a later idea with the
  hardware test it needs.
- Show the base model's name in the picker; tier labels alone leave users asking which
  model it is.

## Answering "does it run on GPU generation X?"
- Read the pinned engine's CUDA build, not forum claims: `scripts/cuda-archs.py
  <ggml-cuda.dll>` lists the SASS/PTX compute capabilities in its fatbin (75 = Turing,
  86 = Ampere, 89 = Ada, 120 = Blackwell). Plain `grep -a sm_75` misses them (the arch is
  a binary field, not text).
- Add the minimum driver (from the CUDA toolkit the engine was built with) and whether
  that generation still gets it; then map the generation's memory sizes onto the measured
  tiers.
- Answer "in theory, from the build" + "never tested on a real card of that series" +
  slower, with no number.
- Arm PCs are not covered by an x64 build; never claim them.

## Hardware-check wizard
1. Detect GPU name, VRAM, driver vs runtime minimum, system RAM, free disk.
2. Label every model against the CARD, not the live free VRAM: usable = total VRAM minus
   a fixed OS/desktop reserve measured once. Live free VRAM makes every model "Too big"
   while the app's own job holds the card, and blames the app for another program's load.
   Other apps' usage is at most a soft note at submit time, never a block. Put the
   calculation in ONE function so a unified-memory platform later changes only that
   function. Labels:
   - 🟢 Full GPU — fastest
   - 🟡 Partial offload — runs, slower; show the MEASURED slowdown factor
   - 🔴 Too big — hidden behind "show all" with the reason
3. Small cards must always get at least one runnable option; never block a PC that has
   enough VRAM + RAM combined.
4. Re-check the label before each job (inputs change memory use) and warn instead of
   failing. The fit note names every input it assumed.
5. Settings → Models: download other models with their label, delete, disk use.
6. Gate the wizard on disk state, not only a "first run done" flag: a reinstall after the
   models were deleted must reopen the wizard.
7. Downloads run one file at a time (first-needed file usable first, exact resume).

## Measuring the thresholds
- The label formula's constants come from a coder feasibility spike, never from
  estimates: run each model at the default size with a VRAM cap to simulate smaller cards,
  record peak VRAM + seconds, pin them in code with tests over a table of fake GPUs.
- Run the spike only on a free GPU: check what else holds the card first; a shared GPU
  spills to RAM and the numbers are wrong.

## Distribution beyond the owner
- Every error = a plain sentence + what to do, never a traceback; a "Copy diagnostic
  report" button (versions, GPU, VRAM, last engine error — never user content).
- Content-sensitive models get a one-time notice the first time they are shown; the
  choice is remembered.
- Unsigned exe: say up front that SmartScreen shows "More info → Run anyway" and plan an
  illustrated mini-guide.

## Privacy defaults to ask about at kickoff
- Prompts in output-file metadata travel with a shared file: default to keeping settings
  in the app's own history only, output files clean. Check whether the engine itself
  writes the prompt into the file, and strip it.
- Engine logs that contain user input are deleted on success. Agent tests on real
  hardware use neutral, safe inputs only.
