# Briefing a fleet agent to produce a public-facing asset

For a logo, demo GIF, banner, social preview or screenshot set produced by a
sibling agent. These are the failure modes a code brief does not have: the
constraint can be too broad, and the scene can be the wrong one. Both yield
work that is technically correct and worse than what it replaces.

## Before briefing at all: is the asset needed?

**Name the artifact that already answers the question the asset would answer,
and say why it is insufficient.** A README with a workflow diagram, a
screenshot set and a banner may already cover the promise; an animated demo
then adds megabytes and review cycles for a marginal gain. Write that sentence
before the brief — if it cannot be written, the asset is not needed.

**Treat repeated rejection as evidence about the goal, not the execution.**
When two or three passes each produce competent work that gets rejected for a
different reason, the scene keeps moving because the underlying need was never
sharp. Stop and re-ask what problem the asset solves rather than writing
another brief.

## Constraints

**Narrow a safety constraint to the actual risk, and name the permitted
substitute.** "No faces at all" is obeyed literally and yields grey placeholder
boxes; the real rule is "never a real person's photo", and a project's **own
generated art** — already committed, already public, often already declared in
the README — is both allowed and the better choice. A blanket prohibition the
agent cannot reason around costs the deliverable's whole appeal, and it will not
push back because it reads as caution.

**Never publish third-party pixels.** Ask where a reference image came from
before building on it, and regenerate an original in that style for the final
asset. Someone else's pixels in a permissively-licensed repo block publication.

## Inputs

**Point it at the repo's own script that produced the existing assets**, not at
the assets themselves. Regenerating from the same generator guarantees the new
asset matches what is already published; cropping or re-creating the inputs by
hand guarantees it does not. `git ls-files` plus a grep for the source image
name finds that script. Check its dependencies are already cached before
briefing — a model download the brief does not mention becomes the agent's
problem mid-job.

**Every value comes from the project's shared token file**, and where one is
genuinely absent the agent falls back to the stylesheet the tokens were
generated from and marks each use. Require the gap list back alongside the
finished asset; it is a real finding about the source, not an obstacle.

## Scene

**Choose the scene the product's own promise names, not the screen that is
easiest to animate.** A demo of the path taken when the tool is *unsure*
advertises the exception, not the product. Read the README's opening claim and
script the arc that demonstrates it.

**Script the README's own opening diagram, beat for beat.** Projects state
their workflow at the top as a chain of steps; that chain is the storyboard,
and the beat most often dropped is the *first* one — the setup that teaches the
tool what it needs. Without it the product's core behaviour looks like magic
rather than something earned, which undercuts exactly the trust the demo
exists to build.

**Measure the time split across beats before accepting a sequence.** Sum the
hold durations per section from the source: one beat occupying two thirds of
the runtime is the "wrong scene" failure in quantitative form, and a section
that is nearly all held frames is padding rather than content. Derive both from
the timing constants, not by watching.

**Set a minimum hold per text block in an explainer brief: ~5 s for a 3-4 line step, more on a phone.** 3 s per multi-line step is too fast to read; the sibling cannot judge pace without a number.

**Cap it at one continuous story, not a tour.** Three seconds per screen across
four screens teaches nothing. Name the stop point explicitly in the brief.

## Wording on a public-facing image

An asset can be visually right and still fail as a presentation because its
labels are written for the people who built the thing.

**Ban command names, flags, folder names and file extensions from labels.** The
audience for a README diagram or banner does not know what `--apply`, `_review/`
or `--json` are, and a label naming one teaches nothing at a glance. Technical
precision of that kind belongs in the README body where there is room to define
it; the image carries the idea.

**Pair "make it simpler" with "and still true" in the same instruction.** Plain
wording drifts into claims the product does not make — a step relabelled "files
them away" when nothing moves without an explicit confirmation flag is now a
lie, and on a diagram whose whole point is that the tool does not act behind
your back it destroys the thing being advertised. Name the specific guarantee
the simplification must not erase.

**On a README top, every line does one job and none repeats its neighbour.**
The header is the mark, the name and a tagline; the line beneath it already
states the full promise. Judge a tagline against that line, not in isolation —
the option that sounds most complete alone often restates the sentence below
it ("locally" over "on your own machine"), while the shortest one lets the
tagline say *what* and the line say *where*, and leaves the mark larger. Say
which you would pick and why, rather than relaying the sibling's pick.

**A bare mark is too thin for a README header; a lockup is the usual fix.**
Mark on the left, name beside it in the display font, a 2-4 word tagline in
small spaced capitals under the name, light and dark SVGs through one
`<picture>` tag. Ask for the letters as outlined paths: GitHub renders a README
SVG as a plain image that cannot load web fonts. Keep the wide banner for the
social preview — the README header and the link card are separate decisions.

**The social preview is uploaded by hand, by the user, and only once the repo is
public.** GitHub hides the Social preview setting on a private repo that has
never had one, so its absence is not a bug to chase; no agent can set it. Check
the image is already compliant (under 1 MB, at least 1280x640, 2:1) so the
upload is one click on publication day, and tell the user the menu path.

**Ask for the draft before the commit when the change is wording.** Label
phrasing is taste, it is cheap to iterate in a draft directory, and committing a
guess costs a regeneration plus a revert.

## README structure for a tool with both a window and a command line

**Write the README for the person with the problem, not for the interface the
tool grew from.** When a CLI-first tool gains a GUI, its README usually still
teaches every step as a command. Lead with the window: logo, the problem, what
it will not do, install, the steps done in the window, how it decides, privacy,
licence. Move the command walkthrough, the command reference, the
scripting/agent sections and remote use to `docs/cli.md`, linked by one line
near "Use" that names both audiences ("prefer the command line, or letting an
assistant drive it?"). Moved, never deleted, and keep the agent-driving use
visible in that line: it is a rare strength, not an appendix.

**Require each window step to be checked against the app's UI code before it is
written.** A README that promises in the window something only the CLI can do is
false in a way no test catches. Ask the sibling to classify every step as
window-only, CLI-only or both, and keep a CLI-only step as a command with a link.

**Land the visual change and the restructure as two commits.** A header/image
commit is a small reviewable diff; a README reorganisation is a large one, and
mixing them makes neither revertible on its own. Close the pending approval
first, then dispatch the restructure as a separate job.

**Before okaying a file deletion in a sibling's commit, grep the whole repo for
the filename.** An image retired from the README may still feed a test, a
generator or a private script; `grep -rln '<stem>' --include='*.py' --include='*.md' .`
settles it, and a hit only in tests that build their own fixtures is not a
consumer.

**Verify a multi-screen sequence exists in the app before scripting it.** Grep
the UI source for the transition and use its exact copy and animation class;
when the app chains the screens itself the demo reports behaviour rather than
montaging it, which is both more honest and less work to defend.

## The bar

**Set it as "must beat what it replaces", and grant permission to reject its own
output.** Ask for an honest side-by-side judgement against the current artifact
and say the deliverable is dropped if it only ties — bytes served on every page
view have to earn their place. Without that clause the agent optimises for
finishing.

**Weigh the asset against the page's whole existing payload, not against the
brief's cap.** Sum the bytes of every image the document already serves; an
asset inside its stated limit can still exceed that total single-handedly. When
it does, the lever is REPLACEMENT, not recompression — dropping resolution and
frame rate typically buys a small fraction back for visible quality loss, while
retiring the still it supersedes nets far more. Measure both before advising.

**Name where the asset lands, and what it does *not* replace.** A demo added
near the top of a README answers "what does this do"; the screenshot deeper in
answers "what does it look like". Two jobs, two artifacts — saying so prevents
the agent, and you, from deleting a good still.

## Size: find where the bytes are before cutting anything

**Ask for a per-frame byte measurement before accepting any proposal to cut.**
In a delta-encoded animation the cost is wildly uneven: still frames are nearly
free, and essentially the whole file lives in the frames where a *photographic*
region moves or fades, because no pixels can be reused there. The consequence
is counter-intuitive and decides the whole negotiation — trimming a long static
intro saves almost nothing, so the real budget unit is the NUMBER OF MOTION
EVENTS, not the duration.

**Cut repeats by rebuilding the scenario smaller, never by truncating the
sequence.** When one interaction repeats N times, most of those repeats are
paid-for restatement of an idea already landed; the fix is a smaller test world
with the engine re-run over it, so the demo ends honestly on its own terms.
Require that every count still come from the real engine — a hand-written
number chosen to hit a size target is a fabricated result, however small.

**Re-encoding into another animated container is not a size rescue for
photographic motion — measure it rather than proposing it.** Animated WebP at
several qualities can land equal to or heavier than a well-palettised GIF of
the same footage. One measurement closes the option; an assumption reopens it
every session.

**Never truncate a sequence to a point where its final state contradicts the
product's claim.** Dropping the last iterations of a queue-draining demo is the
cheapest byte saving available and the one to refuse: an empty-state ending
("nothing waiting") IS the thesis, and a loop that restarts with work still
pending advertises the opposite of the README. Trade resolution, frame rate or
scope before trading the honesty of the ending.

**A cap you set yourself is revisable evidence, not a fixed requirement.** When
the agent's measurements show the number cannot be met without cutting
substance, check what unit you set it in — an asset's own size is the wrong one
when it supersedes several existing files, and the net delta after retiring
them is often acceptable where the gross figure was not. Say plainly that the
limit was yours and wrong; a sibling will otherwise keep cutting against it.

**Separate the agent's measured numbers from its estimates and weight them
differently.** A good report labels which is which; decide on the measured
ones, and treat an estimated saving as a reason to measure, never as a reason
to cut.

## Explainer video about one of the owner's own agents or tools

The ask is "show my friend what X is, how I built it, what it gives back and
why". No README diagram to script from, usually no brand. The brief shape
that works, in `<media-workspace>/JOB-NNN/BRIEF.md`:

- **Facts section, written by the coordinator, with the source file for each fact**
  (the agent's SOUL, its procedure skill, the project README/SCHEMA, counts
  from the repo). Say "these are the ONLY source of truth; verify read-only".
  The sibling then traces every on-screen number to a file in its report, and
  the coordinator checks that list instead of re-deriving.
- **No `tokens.json` is not a blocker for a private explainer.** The motion
  agent's SOUL stops on a missing design folder; state that the owner's request IS
  the say-so, have it write a job-local `tokens.json` (calm palette, verdict
  colours mirroring the product's emoji/status colours, fonts already present
  in the media workspace), and forbid creating `.design/` in the project repo.
- **Beats with a time budget each** (problem → one-sentence what → the
  pieces as one diagram → the pipeline as a chain → the output card line by
  line with a 3-6 word "why" beside each → memory → close), one continuous
  story, 60-100 s. Ask for the measured split back.
- **Language of the on-screen text = the audience's**, and keep the product's
  real labels verbatim (a card that is in another language in real life stays
  in that language). Tell the owner the choice in one line; it is reversible.
- **Phone delivery spec**: 1920x1080, 30 fps, H.264, `+faststart`, ≤ 25 MB
  (chat apps then send it as a video), silent is fine, body text ≥ ~40 px.
- **"Simpler and still true"** named for this product: nothing on screen may
  claim the agent installs or runs the tools when it is read-only.
- **Use a real record as the example** (one wiki page / one entry) and say
  "if the page lacks a value, leave that line out" — never a made-up number.
- **Work-clean section, and repeat the owner's words in the dispatch prompt**
  ("the owner's explicit words for this job: work clean"). Require: everything
  under the job folder, project repo and sibling profiles read-only, no
  installs, build cache / raw render / scratch deleted at the end with paths
  listed, and `TEMP`/`TMP` pointed at a job-local `_work/tmp` so the engine's
  chunk files never land in the system Temp.
- **Keep ≤ 8 check frames in `check-frames/` for the coordinator, who deletes them.**

The coordinator's own check on return, before sending: `ffprobe` (size, fps, duration),
one contact sheet of a frame per beat, then one full-res frame for text size:

```
ffmpeg -v error -y -i out.mp4 -vf "select='eq(n\,F1)+eq(n\,F2)+...',scale=640:-1,tile=4x2" \
  -frames:v 1 -fps_mode vfr contact.png     # ffmpeg ≥ 7: -vsync is gone, use -fps_mode
```

Then `rm -rf check-frames` — if it says "Device or resource busy" seconds after
the sibling exited, its runtime still holds a handle; wait a few seconds and
retry rather than leaving the folder. Deliver the file by path, report the
beats, what the coordinator verified, what was removed, what stays (video + source for
re-render), and the one judgement only the owner can make (pace, wording).

## Verifying what comes back

`ffprobe` confirms size, fps and duration while the picture is wrong. Extract
frames at the boundaries and look at them; `md5sum` the first and last frame of
a looping asset rather than eyeballing the seam. Prove derivation with
`grep -rnoE '#[0-9a-fA-F]{6}'` over the generator source (must be empty) and
`md5sum` of its copy of the token file against the one in the project repo.

**Read the generator source before proposing an animation change.** A
transition that looks expensive may be a faithful port of the app's own
behaviour, in which case the agent is right and the cost is intrinsic — check
the app's UI source for the same class or function before suggesting it be
simplified.
