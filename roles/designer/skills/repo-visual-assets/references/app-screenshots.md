# App screenshots for a README / social preview

Screenshots of the REAL running app, reproducible by script, safe to publish.

## Procedure

1. **Build a public world.** A fixture script (kept in the project's private spikes)
   that builds inputs from the repo's own public art or other licence-clean samples
   only - e.g. crop a generated image into several varied inputs (pad, gain, flip),
   plus the edge cases the app handles (several subjects in one input, an input with
   none). Fictional names. Check first that the app's own code finds every subject
   in the world (run it once and count), or the world silently lacks a case.
2. **Hide the machine.** Paths show up in the window (library chips, source fields).
   Map the world folder to a short drive or path before launching:
   Windows `subst.exe V: 'C:\...\scratch\world'` (from git-bash call `subst.exe`, and
   remove with `subst.exe V: /D` - `//D` is rejected); Linux/mac: a short symlink like
   `/tmp/demo`. Launch the app with its data dir on that path too.
3. **Drive the real flow, not shortcuts.** Seed only what a user would set up first
   via the CLI; let the window do the main flow (e.g. preview -> apply -> review), so
   counts, history and badges are the ones a user sees. Stub only native dialogs
   (folder pickers) in the driver.
4. **Frame each shot deliberately.** Pick the most telling item (e.g. jump a review
   queue to its richest case), wait until images are decoded (`naturalWidth > 0`),
   and wait for transient UI (toasts, spinners) to be GONE before capturing -
   a toast left in frame is the most common flaw.
5. **Pick 3-4 shots, one purpose each.** Hero = the core interaction; a pair
   table for secondary screens; one shot of the other theme. Drop screens that are
   mostly empty (a one-row history). Look at every shot with vision before keeping it.
6. **Commit** under `docs/assets/screens/`, re-saved through Pillow (`optimize=True`,
   no text chunks), and document in docs/assets/README.md what they show and that
   they must be retaken after visible UI changes. Keep the fixture + driver scripts so
   a retake is one command.
7. **Social preview** drawn by a small script (name + tagline left, the hero screenshot
   right, rounded corners, soft shadow, bleeding toward the edge), 1280x640, house
   fonts/colours. Remind the owner to upload it in GitHub Settings -> Social
   preview; git does not deliver it.

## Pitfalls

- Rebuild the world only after closing the app: it may hold the database open, and
  a delete under it leaves a half-deleted world with no error.
- A one-way action run once in the world (an apply, a move) cannot be re-previewed:
  rebuild the world for every screenshot pass instead of trying to reset it.
- README claims about the UI (keys, theme behaviour, launch command, data folder)
  must be checked against the code before commit, not written from memory.
