# Demo / explainer video phase (media, headless)

After the packaged app is verified: a video that says what the version brings and shows
how it is used, in the end user's language, with music. Everything below goes into the
video brief; dispatch it like any headless job and verify from disk.

## What the coordinator writes itself: the Facts section
media may only claim what the Facts list says. Write it from `CHANGELOG.md` + README +
what you verified yourself (folder layout, default paths, quit paths, privacy). Anything
not in Facts is left out of the script, even if the brief's own prose implies it.

## Visual material: real screens, real data
- Launch the app from source with `<APP>_HOME` → scratch and `--no-browser`; drive it in
  a headless browser; the design mockups are the expected look. State the network
  budget as numbers (how many searches, downloads, pages).
- Allow drawn stand-ins only where a real run cannot show the state (an old version's
  screen, a failure/retry row) and require the REPORT to list every drawn element.
- Scratch paths leak into settings screens: require a blur or a clean path, and check
  the frames for them.
- Raw captures that contain third-party content stay OUT of git; the repo gets the
  script, storyboard, credits and renders. Ask for the working-project path in the REPORT.

## Script
problem → solution → how (3-4 UI beats) → payoff → end card (logo, one install line).
60-90 s, ~2.3 words/s, captions burned in, plain language. Captions must never cover the
UI's primary button — say it, media checks it.

## Audio (state the policy, let media measure)
- Narration LOCAL first (a local TTS installed only in a venv under the project), with a
  listen-check sample saved to `_job/`. Some local voices garble short key words: the
  sample is how you find out. A cloud TTS fallback is allowed only if marked CLOUD in the
  REPORT; repeat that to the owner plainly and offer to redo it locally.
- Music: CC0 or CC-BY only, licence text saved under the video's `credits/` folder,
  credit on the end card and in `CREDITS.md`, ducked ~14 dB under speech, fade on the end
  card.

## Deliverables and the coordinator's check
- `assets/<App>-<ver>-demo.mp4` (H.264 + AAC, `+faststart`, ≤ 90 s) and a 10-15 s silent
  GIF for the README (≤ 4 MB).
- Verify with ONE contact sheet, not by watching:
  `ffmpeg -i demo.mp4 -vf "select='not(mod(n\,180))',scale=640:-1,tile=3x5" -frames:v 1 sheet.png`
  (write it to an absolute scratch path), then one vision call: captions readable,
  nothing cut off, no private paths, right theme. Delete the sheet in the sweep.
- Deliver the file by path; tell the owner the voice/music choice and licences in two
  lines.
