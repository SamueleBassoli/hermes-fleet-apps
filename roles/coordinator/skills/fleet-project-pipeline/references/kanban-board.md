# Kanban board: diagnosing a card that loops or blocks

Order, cheapest first:

1. `hermes kanban list` and `hermes kanban diagnostics`: state of every card and the
   active alerts.
2. `hermes kanban show <id>`: body, result, comments, then the events and runs. Read the
   events: a `claimed` with `source_status: review` means the review lane spawned it;
   `crashed` + `gave_up` after `failure_limit` means it was blocked automatically.
3. The worker's log: `kanban/logs/<id>.log` under your Hermes home. The real error is at
   the tail (e.g. `Error: Unknown skill(s): ...`); the event's `worker_output` shows only
   the last chat lines, which can look like success.
4. Which process dispatches: the event's `lock` is `<host>:<pid>`; that pid is the
   `gateway run` process. Its launch profile (the home holding `gateway.pid`) is where
   dispatcher settings take effect.
5. Settings: `hermes -p <launch profile> config get kanban` (`review_dispatch`,
   `failure_limit`, `dispatch_interval_seconds`). Read each tick; no restart needed.

Pitfalls:
- "In progress" right after an unblock is not the agent working: `unblock` returns the
  card to its resume status (often review), and if the review lane is on it respawns and
  fails again. Fix the cause before unblocking.
- After a fix, `unblock` and wait at least two dispatcher ticks before reporting it works.
