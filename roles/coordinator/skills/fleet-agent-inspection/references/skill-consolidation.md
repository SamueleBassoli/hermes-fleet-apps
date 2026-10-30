# Consolidating near-duplicate skills in a profile

Profiles accrete skills that overlap: three that all cover a project's visual
assets, written months apart under slightly different names. Merging is a
deletion, so it is done with a net.

On a **sibling** agent's profile this needs the user's explicit say-so first —
another agent's skills are another agent's state. Once they ask, do the whole job
rather than deleting the obvious duplicates and stopping.

## Procedure

```bash
cd $HERMES_HOME/profiles/<name>
mkdir -p backups/skills
tar -czf backups/skills/<topic>-pre-merge.tar.gz skills/<each candidate dir>
```

1. **Back up every candidate first, including the survivor.** The survivor gets
   edited too, so a merge that goes wrong should cost one `tar -xzf` rather than
   months of accrued corrections.
2. **Read each candidate in full and pick the survivor by body weight, not by
   the most appealing name.** The longest, most-corrected body carries the real
   lessons; keeping a shorter skill because its title reads better throws the
   substance away and keeps the label.
3. **Diff for lessons that live in exactly one file, and copy them into the
   survivor before deleting anything.** Each doomed skill typically holds two or
   three rules found nowhere else — those are the entire reason the file was
   worth keeping, and `rm -rf` loses them silently with no error.
4. **Grep the whole skills tree for the doomed names before deleting.** Another
   skill may point at one by name; the pointer goes dead and a future session
   follows it to nothing.
5. **Check `references/` as well as `SKILL.md`.** A thin body can sit on top of
   substantial reference files, which is invisible from a line count of the body
   alone.
6. **Report which files were deleted, where the backup is, and which lessons
   were carried across.** "Consolidated 3 into 1" is not a reviewable claim.

## After the merge

Re-measure the profile's per-turn cost so the consolidation has a number
attached rather than a feeling:

```bash
hermes -p <name> prompt-size | head -15
```

Skill index lines are cheap in the prompt (~80 B each); the real win of a merge
is attention and the absence of three files that disagree with each other.
