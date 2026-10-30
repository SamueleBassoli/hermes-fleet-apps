# Source in a terminal call:  . <skill>/scripts/kanban-card.sh
# mk "<title>" <assignee> <workspace dir> "<body>" [parent-id]   -> prints the card id
#
# Creates a kanban card from a body file (quotes and newlines survive), then subscribes the
# owner's chat with notify+wake, so done/blocked reaches the owner AND wakes the coordinator.
#
# Settings come from the environment, never from this file:
#   KANBAN_NOTIFY_PLATFORM   messaging platform of the owner's chat (e.g. telegram)
#   KANBAN_CHAT_ID           chat id of the owner's chat
#   KANBAN_THREAD_ID         optional thread/topic id
#   KANBAN_NOTIFIER_PROFILE  profile that receives the wake (default: coordinator)
#   KANBAN_CREATED_BY        creator recorded on the card (default: coordinator)
# Without KANBAN_NOTIFY_PLATFORM and KANBAN_CHAT_ID the card is created but not subscribed.
#
# <workspace dir> must be a native absolute path (C:/... on Windows): the body file is written
# in <workspace>/_job/ (keep _job/ in .gitignore); a body under $TMPDIR can resolve to a path
# hermes cannot open, and the create then fails with empty output.
# Refuses a body carrying a session token ("token="): a card body is stored on the board and
# read by another model. Point the card at HOW to read the token instead.
# Use this helper rather than hand-written `hermes kanban create` lines, so the token check
# always runs.
mk(){
  case "$4" in *token=*) echo "REFUSED: card body contains token=" >&2; return 1;; esac
  mkdir -p "$3/_job"
  local body="$3/_job/card-$$.txt"; printf '%s\n' "$4" > "$body"
  local args=(kanban create "$1" --assignee "$2" --workspace "dir:$3" \
    --created-by "${KANBAN_CREATED_BY:-coordinator}" --body-file "$body" --max-retries 1 --json)
  [ -n "$5" ] && args+=(--parent "$5")
  local out id; out=$(hermes "${args[@]}" 2>&1)
  rm -f "$body"
  id=$(printf '%s' "$out" | python -c "import sys,json
try: print(json.load(sys.stdin)['id'])
except Exception: pass")
  if [ -z "$id" ]; then echo "CREATE FAILED: $out" >&2; return 1; fi
  if [ -n "$KANBAN_NOTIFY_PLATFORM" ] && [ -n "$KANBAN_CHAT_ID" ]; then
    local sub=(kanban notify-subscribe --platform "$KANBAN_NOTIFY_PLATFORM" \
      --chat-id "$KANBAN_CHAT_ID" --chat-type dm \
      --notifier-profile "${KANBAN_NOTIFIER_PROFILE:-coordinator}" --delivery-mode notify+wake)
    [ -n "$KANBAN_THREAD_ID" ] && sub+=(--thread-id "$KANBAN_THREAD_ID")
    hermes "${sub[@]}" "$id" >/dev/null 2>&1 || echo "SUBSCRIBE FAILED for $id" >&2
  fi
  echo "$id"
}
# Append every id to the job's CARDS.txt (e.g. echo "c7=$id" >> _job/CARDS.txt) so a later
# session finds the card graph without scanning the whole board.
