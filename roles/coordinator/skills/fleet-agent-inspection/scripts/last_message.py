#!/usr/bin/env python3
"""Print the tail of another Hermes profile's conversation.

Usage:
    python last_message.py <profile>                 # its last assistant reply
    python last_message.py <profile> -r any -n 6     # last 6 messages, any role
    python last_message.py <profile> --sessions      # recent sessions

Opens $HERMES_HOME/profiles/<profile>/state.db READ-ONLY, so it is safe to run
while that profile's own session is live and holding the WAL.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import sqlite3
import sys
from pathlib import Path


def hermes_home() -> Path:
    env = os.environ.get("HERMES_HOME")
    if env:
        return Path(env)
    if os.name == "nt":
        return Path(os.environ["LOCALAPPDATA"]) / "hermes"
    return Path.home() / ".hermes"


def connect(profile: str) -> sqlite3.Connection:
    db = hermes_home() / "profiles" / profile / "state.db"
    if not db.exists():
        sys.exit(f"no state.db for profile {profile!r} at {db}")
    # as_posix(): a sqlite URI containing backslashes does not parse on Windows
    return sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)


def stamp(ts) -> str:
    try:
        return dt.datetime.fromtimestamp(float(ts)).strftime("%m-%d %H:%M")
    except (TypeError, ValueError):
        return str(ts)


def recent_sessions(con: sqlite3.Connection, limit: int = 5) -> list:
    # group on messages, not sessions: sessions.message_count lags behind
    return list(
        con.execute(
            "select session_id, max(timestamp) t, count(*) from messages "
            "group by session_id order by t desc limit ?",
            (limit,),
        )
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("profile")
    ap.add_argument("-r", "--role", default="assistant",
                    help="assistant (default), user, or any")
    ap.add_argument("-n", "--count", type=int, default=1)
    ap.add_argument("-c", "--chars", type=int, default=4000,
                    help="truncate each message at N chars")
    ap.add_argument("-s", "--session", help="session id (default: most recent)")
    ap.add_argument("--sessions", action="store_true",
                    help="list recent sessions and exit")
    a = ap.parse_args()

    con = connect(a.profile)
    sessions = recent_sessions(con)
    if not sessions:
        sys.exit("no messages recorded in this profile")

    if a.sessions:
        for sid, ts, n in sessions:
            print(f"{stamp(ts)}  {sid}  {n} msg")
        return

    sid = a.session or sessions[0][0]
    where = "session_id = ? and content is not null and length(content) > 0"
    params: list = [sid]
    if a.role != "any":
        where += " and role = ?"
        params.append(a.role)
    params.append(a.count)

    rows = list(
        con.execute(
            f"select role, content, timestamp from messages where {where} "
            "order by timestamp desc, id desc limit ?",
            params,
        )
    )
    if not rows:
        sys.exit(f"no {a.role} messages in session {sid}")

    print(f"# profile {a.profile}  session {sid}")
    for role, content, ts in reversed(rows):
        body = content if len(content) <= a.chars else content[: a.chars] + "\n[...truncated]"
        print(f"\n--- {role} @ {stamp(ts)}\n{body}")


if __name__ == "__main__":
    main()
