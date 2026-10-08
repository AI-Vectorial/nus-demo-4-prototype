#!/usr/bin/env bash
# Start both services. Safe to run again -- it skips whatever is already up,
# and waits for a port to be released rather than racing it.
#
# That race is not hypothetical: killing a dev server and restarting it two
# seconds later fails with EADDRINUSE, the new process dies, and the port is
# then free with nothing on it. Every later check says "connection refused"
# while the log blames a port that is no longer in use.
set -uo pipefail

cd "$(dirname "$0")/.."

# The same key selection every terminal gets -- see credentials.sh.
. "$(dirname "$0")/credentials.sh"
if [ -n "${OPENROUTER_API_KEY:-}" ]; then
  echo "credentials: using the key for table ${TABLE_ID:-?}"
fi

listening() { ss -ltn 2>/dev/null | grep -q ":$1 "; }

wait_free() {
  local port="$1" n=0
  while listening "$port" && [ "$n" -lt 30 ]; do sleep 1; n=$((n + 1)); done
  listening "$port" && return 1 || return 0
}

wait_up() {
  local port="$1" n=0
  while [ "$n" -lt 60 ]; do
    curl -sf -o /dev/null --max-time 5 "localhost:${port}" 2>/dev/null && return 0
    sleep 2; n=$((n + 1))
  done
  return 1
}

# --- backend ----------------------------------------------------------------
if listening 8000; then
  echo "backend   already running on :8000"
else
  (cd backend && nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 \
    > /tmp/backend.log 2>&1 &)
  echo "backend   starting on :8000"
fi

# --- frontend ---------------------------------------------------------------
# -H 0.0.0.0 is in package.json's dev script. Next binds to localhost by
# default, and a loopback-only listener is invisible to the Codespaces port
# forwarder -- curl from the terminal says 200 while the browser gets 502.
if listening 3000; then
  echo "frontend  already running on :3000"
else
  wait_free 3000 || { echo "frontend  :3000 is held by something that will not exit"; exit 1; }
  (cd frontend && nohup npm run dev > /tmp/frontend.log 2>&1 &)
  echo "frontend  starting on :3000 (first compile takes a moment)"
  if wait_up 3000; then
    echo "frontend  ready"
    # Open it ourselves, now that it answers.
    #
    # onAutoForward would do this at bind time, which is before next dev has
    # compiled anything -- the preview opens on a dead socket and says
    # "connection failed". And the forwarded *.app.github.dev URL needs a
    # browser cookie the proxy cannot always get, which is the 502. The
    # in-editor preview goes through the VS Code connection instead, so
    # neither applies to it.
    if [ -n "${BROWSER:-}" ]; then
      "$BROWSER" http://localhost:3000 >/dev/null 2>&1 || true
    fi
  else
    echo
    echo "  !! frontend did not come up. The reason is in /tmp/frontend.log:"
    tail -15 /tmp/frontend.log
  fi
fi

# Port visibility is declared in devcontainer.json, but a port that was ALREADY
# forwarded keeps the attributes it was forwarded with -- so a Codespace created
# before that setting changed, or rebuilt after the port came up, still carries
# the old one. The symptom is a 502 from the forwarded URL while curl from this
# terminal returns 200, which reads as a broken app rather than a blocked one.
#
# Rather than let anyone lose twenty minutes to that, say it up front.
if [ -n "${CODESPACE_NAME:-}" ]; then
  echo
  echo "  Your app is open in the editor preview -- use that."
  echo
  echo "  The forwarded *.app.github.dev URL is a separate thing, and it needs"
  echo "  a port set to Public to work from an outside browser:"
  echo "    PORTS tab -> right-click 3000 -> Port Visibility -> Public"
  echo "  A 502 there is that setting, never a fault in your build."
fi

echo
echo "  frontend  http://localhost:3000   <- your work, live"
echo "  api       http://localhost:8000/docs"
echo
echo "  logs: tail -f /tmp/backend.log  |  tail -f /tmp/frontend.log"
echo
echo "  Read START-HERE.md, then open pipeline/01-shape.md"
