# Supervising a headless sibling job while the owner is away

How the coordinator watches a long headless job (dispatched as in SKILL.md →
"Dispatching headless"), resumes it after a cut, verifies the report and cleans
what the sibling could not.

**Skip all of this for a short daytime job** (cap ≤ 2 h, owner awake, no gate
inside it): the background terminal's completion notice is the signal. The
watchdog earns its place when the job runs overnight, can be cut by a usage
limit, or has a gate (mockup review) inside it.

## 1. Job folder and markers

- In the repo: `BRIEF.md` (definition of done, priority order, hard deadlines:
  stop new work at T-15 min, REPORT + `DONE` by the deadline), `prompt.txt`
  (first start), `resume.txt` ("the session was cut; re-read brief sections X,
  LOG.md, git log/status, continue; if DONE exists stop").
- **One job, one TAG, one set of file names.** A second job in the same repo
  gets its own suffix (`DONE-B`, `MOCKUP2-READY`); shared marker names make one
  job's watchdog act on the other's files.
- Gitignore the marker and prompt patterns so they never land in a commit, and
  tidy the job folder (archive results, delete old logs and markers) before the
  next job in the same repo.
- Input the owner sends after dispatch goes into the brief as a new dated
  section, not into a chat the sibling cannot see.

## 2. Watchdog cron (no-agent script)

Template: `templates/headless_job_watchdog.py`.

- **Print progress lines, not only alarms.** A watchdog silent when all is well
  reads as "forgotten". One heartbeat line per run (the last `LOG.md` entry, ~220
  chars) plus one line per alarm; every 30 min is enough.
- **Create the cron with `no_agent=true` + `script=<filename>` in ONE call**,
  the filename relative to the profile's `scripts/` dir. Without `no_agent` it
  becomes an LLM job that spends tokens every tick; an absolute path is refused.
- **Point the cron at a `.py` wrapper, not a `.sh`**: on Windows the scheduler
  can mangle a `.sh` path's backslashes (exit 127).
- **Prove it fires through the scheduler before saying it is on**: run the
  script by hand, then `action=run`, then `action=list` and read `last_status` /
  `last_error`.
- **Detect liveness by command line, not by the background PID** (that is the
  shell wrapper): match the agent process whose command line contains the job's
  prompt-file path.
- **Do not alarm on repo changes when other agents work in that repo**; attribute
  changes from each profile's `agent.log` instead.
- **Before baselining a real-data hash, check whether the app that owns the data
  is running**: the owner's own use rewrites it and fires a false alarm.
- **Follow-up check**: a one-shot agent cron after the job's expected end, which
  verifies the report and writes a short summary for them.

## 3. When the session ends early

- **Exit code 0 is not success.** A provider error (HTTP 403, auth refusal, a
  usage-limit cut) can end the run cleanly; read the last log lines.
- **Resume the same session; do not restart it**: the work is on disk and in its
  context.

  ```bash
  hermes -p <name> chat -Q --max-turns 600 --resume <session_id> -q "Resume <JOB>. The session was cut at <time> by <cause> (not your fault). Check LOG.md and the files on disk for where you were, then continue the brief."
  ```

- **Kill frozen children it left behind**: a tool that hangs on an error
  survives the session that started it.
- **Context-rot gate**: the brief orders a HANDOFF file after the second context
  compression; the watchdog sees it and the coordinator starts a fresh session
  from it.

## 4. Verifying the report

- **Facts ledger**: `scripts/verify_facts_ledger.py <FACTS.md> <repo>` checks
  every quoted fragment exists within ±2 lines of its cited `path:line`. Zero
  misses = nothing on screen was invented.
- **Read-only repo**: query the sibling's `state.db` read-only for tool calls
  that name protected paths with a write verb (`write_file`, `patch`, `rm`, `mv`,
  `git commit/add/reset`, `sed -i`, `>`). That is proof about the sibling;
  `git status` alone is not when others commit there too.
- **Re-time one benchmark yourself** with the same command, into scratch.
- **Look at the output**: contact sheet plus two full-size frames.
- **Browser checks**: a click that opens a native dialog hangs the browser tool
  until it is answered — answer it in the same call, and forbid native dialogs in
  UI briefs. Toggle controls with real clicks, never by setting `.checked` from
  JS (the app's state listens to events).
- **Two siblings in one repo**: check each one's changes landed in its own
  commit, not swept into the other's.
- **Sweep listeners and dev servers** the sibling started for its screenshots.

## 5. Cleanup the sibling could not do

- Count and size before you delete, then report what was removed.
- Leave a shared folder's other files alone, even when the sibling's own files
  there were the target.
- Then remove the watchdog cron and its scripts, and confirm both are gone.

## 6. Retiring an old tool after an evaluation (on the owner's ok)

1. **Archive learning, not dependencies**: tar the old workspace excluding
   dependency folders (keep the lockfile), plus the retired skill and a
   `RETIRED.md` (why, evidence path, restore command).
2. Verify the archive lists, then delete the workspace.
3. **Grep the whole profile for the old tool's name** — READMEs, references, the
   SOUL — not only the skills you edited.
4. Tool homes outside the repo (`~/.<tool>`) survive deleting the repo: locate
   them too.
5. Undoing a seam in another repo: diff against the last pre-job commit
   (`git diff <pre> HEAD --stat -- <paths>`); a single `git revert` often misses
   parts that travelled in a later commit.

When writing files from Python on Windows inside a git repo, use `newline=""`
(or the file's own line ending), or a five-line change shows as a full rewrite.

## 7. A sibling as an on-demand service (request files)

- **Request = file, answer = file, progress = file**, all in the tool's own home;
  a no-LLM `dispatch` command picks the oldest open request, locks so one agent
  runs at a time, and marks progress older than ~90 min as failed.
- **The serving procedure is a skill in the sibling's OWN profile, written by
  the sibling** during the build job.
- **Prove the first dispatch by hand before trusting the timer**, then leave it
  to the cron.
- After a served request, the coordinator does the git (branch, merge
  `--ff-only` on the owner's word, restart the app).
