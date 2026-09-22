#!/usr/bin/env bash
# Start both services in the background so a table never runs a command to see
# their work. Logs land in /tmp so the terminal stays free for the agent.
set -euo pipefail

cd "$(dirname "$0")/.."

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
