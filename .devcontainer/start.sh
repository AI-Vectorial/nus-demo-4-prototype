#!/usr/bin/env bash
# Start both services in the background so a table never runs a command to see
# their work. Logs land in /tmp so the terminal stays free for the agent.
set -euo pipefail

cd "$(dirname "$0")/.."

# ---------------------------------------------------------------------------
# Credentials.
#
# GitHub injects Codespaces secrets as environment variables, so the key is
# already here -- nobody types, pastes or commits one.
#
# Secrets are repository-wide, so all five land in every Codespace. This picks
# the one belonging to whichever table's branch is checked out, which keeps the
# rate limits separate: five tables embedding a corpus at the same moment on one
# key is the most likely way to stall the whole room at once.
#
# OPENROUTER_API_KEY set directly still wins, so one shared key works for a dry
# run before the five exist.
# ---------------------------------------------------------------------------
if [ -z "${OPENROUTER_API_KEY:-}" ]; then
  BRANCH="$(git branch --show-current 2>/dev/null || echo '')"
  TABLE="$(printf '%s' "$BRANCH" | grep -oE 'table-[1-5]' | head -1 | tr -d 'table-')"

  if [ -n "$TABLE" ]; then
    VAR="OPENROUTER_API_KEY_TABLE_${TABLE}"
    eval "KEY=\${${VAR}:-}"
    if [ -n "$KEY" ]; then
      export OPENROUTER_API_KEY="$KEY"
      echo "credentials: using the key for table ${TABLE}"
    else
      echo
      echo "  !! ${VAR} is not set."
      echo "  !! Your branch is '${BRANCH}', so this Codespace expected that secret."
      echo "  !! Tell an instructor. Do NOT paste a key into a file."
      echo
    fi
  else
    echo
    echo "  !! No OpenRouter key, and branch '${BRANCH}' does not name a table."
    echo "  !! Expected something like 'work/table-3'."
    echo "  !! Tell an instructor. Do NOT paste a key into a file."
    echo
  fi
fi

echo "starting backend on :8000"
(cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 \
  > /tmp/backend.log 2>&1 &)

echo "starting frontend on :3000"
(cd frontend && npm run dev > /tmp/frontend.log 2>&1 &)

sleep 3
echo
echo "  frontend  http://localhost:3000   <- your work, live"
echo "  api       http://localhost:8000/docs"
echo
echo "  logs: tail -f /tmp/backend.log  |  tail -f /tmp/frontend.log"
echo
echo "  Read START-HERE.md, then open pipeline/01-shape.md"
