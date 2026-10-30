"""No-LLM watchdog for a headless coder job (Windows). Copy to <repo>/_job/watchdog.py, fill
the CONSTANTS, point a 3-line runpy wrapper in profiles/<coordinator>/scripts/ at it, and
create the cron with no_agent=true (every 30 min). Prints only when the coordinator must act
or the LOG moved.
"""
import hashlib, json, subprocess
from datetime import datetime
from pathlib import Path

# ---- CONSTANTS (per job) -------------------------------------------------------
JOB = Path(r"<abs path to repo>\_job")
REPO = JOB.parent
TAG = "<PROJECT>-JOB-<date>-<letter>"          # also the first words of prompt.txt
CMDLINE_MATCH = "*<repo>/_job/*.txt*"           # unique per job: prompt/resume file path
REAL_DB = Path(r"<abs path to the user's real data file>")  # the data the brief fences
BASE_HASH = "<sha256 of REAL_DB at dispatch>"
DEADLINE = datetime(2026, 1, 1, 9, 0)           # no restarts after this
MAX_RESTARTS = 3
AGENT = "coder"                                 # profile that runs the job
SUFFIX = ""                                     # "-B" for a second job in the same repo
# -------------------------------------------------------------------------------
STATE = JOB / f"state{SUFFIX}.json"
DONE, HANDOFF = JOB / f"DONE{SUFFIX}", JOB / f"HANDOFF{SUFFIX}.md"
MOCK_READY, MOCK_OK = JOB / f"MOCKUP{SUFFIX}-READY", JOB / f"MOCKUP{SUFFIX}-OK"


def alive():
    ps = ("Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*hermes*' -and "
          f"$_.CommandLine -like '{CMDLINE_MATCH}' }} | Measure-Object | Select-Object -ExpandProperty Count")
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True).stdout.strip()
    return out not in ("", "0")


def main():
    st = json.loads(STATE.read_text()) if STATE.exists() else {"restarts": 0, "last_log": ""}
    log = REPO / "LOG.md"
    last = log.read_text(encoding="utf-8", errors="ignore").strip().splitlines()[-1][:220] if log.exists() else "(no LOG yet)"
    msgs = []
    if REAL_DB.exists() and hashlib.sha256(REAL_DB.read_bytes()).hexdigest() != BASE_HASH:
        msgs.append("ALARM real db changed (hash differs from baseline) - attribute before alarming the owner")
    if DONE.exists():
        msgs.append(f"DONE | {last}")
    elif HANDOFF.exists():
        msgs.append(f"HANDOFF written - the coordinator must start a fresh {AGENT} session from {HANDOFF.name}")
    elif MOCK_READY.exists() and not MOCK_OK.exists():
        msgs.append(f"MOCKUP READY - the coordinator must review the shots and write {MOCK_OK.name}")
    elif not alive():
        if datetime.now() < DEADLINE and st["restarts"] < MAX_RESTARTS:
            n = st["restarts"] + 1
            cmd = (f'cd /d "{REPO}" && hermes -p {AGENT} chat -Q --yolo --max-turns 500 '
                   f'--query-file "{JOB / f"resume{SUFFIX}.txt"}" > "{JOB / f"session{SUFFIX}-{n+1:02d}.log"}" 2>&1')
            subprocess.Popen(cmd, shell=True, creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0) | subprocess.DETACHED_PROCESS)
            st["restarts"] = n
            msgs.append(f"{AGENT} was not running - restarted ({n}/{MAX_RESTARTS}) | {last}")
        else:
            msgs.append(f"STOPPED and not restarted (deadline or max restarts) | {last}")
    elif last != st.get("last_log"):
        msgs.append(f"running | {last}")
    st["last_log"] = last
    STATE.write_text(json.dumps(st))
    if msgs:
        print("\n".join(msgs))


if __name__ == "__main__":
    main()
