#!/usr/bin/env bash
#
# Get a table from a fresh Codespace to "ready to prompt" in one command.
#
#   ./scripts/quickstart.sh 3
#   ./scripts/quickstart.sh facilitator
#
# Checks what actually has to be true, fixes what it safely can, and refuses
# to pretend. It does not build anything and it does not answer any decision.
#
set -uo pipefail

N="${1:-}"
[[ "$N" =~ ^([1-5]|facilitator)$ ]] || { echo "usage: $0 <table number 1-5 | facilitator>"; exit 1; }

# 3 -> table-3, facilitator -> facilitator
SLUG="table-${N}"; KEYVAR="OPENROUTER_API_KEY_TABLE_${N}"
[[ "$N" == "facilitator" ]] && { SLUG="facilitator"; KEYVAR="OPENROUTER_API_KEY_FACILITATOR"; }

ok()   { printf '  \033[32mok\033[0m    %s\n' "$1"; }
bad()  { printf '  \033[31mFAIL\033[0m  %s\n' "$1"; FAILED=1; }
note() { printf '        %s\n' "$1"; }
FAILED=0

echo
echo "${SLUG} -- checking the things that have to be true"
echo

# --- the branch -------------------------------------------------------------
CURRENT="$(git branch --show-current 2>/dev/null || echo '')"
WANT="work/${SLUG}"
if [[ "$CURRENT" == "$WANT" ]]; then
  ok "branch          ${CURRENT}"
elif [[ "$CURRENT" == "${SLUG}" ]]; then
  git checkout -q -b "$WANT" && ok "branch          created ${WANT}"
else
  bad "branch          on '${CURRENT}', expected ${SLUG} or ${WANT}"
  note "git checkout ${SLUG} && git checkout -b ${WANT}"
fi

# --- the key ----------------------------------------------------------------
# start.sh exports it for the servers; ~/.bashrc exports it for every terminal.
# An older Codespace has neither, so fall back to the secret directly.
if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  eval "FALLBACK=\${${KEYVAR}:-}"
  [[ -n "$FALLBACK" ]] && export OPENROUTER_API_KEY="$FALLBACK"
fi
if [[ -n "${OPENROUTER_API_KEY:-}" ]]; then
  ok "openrouter key  ${OPENROUTER_API_KEY:0:14}..."
else
  bad "openrouter key  not set, and ${KEYVAR} is empty"
  note "Tell an instructor. Do NOT paste a key into a file."
fi

# --- the stores -------------------------------------------------------------
# docker is deliberately absent -- postgres and qdrant are sibling containers.
HEALTH="$(curl -s --max-time 10 localhost:8000/healthz 2>/dev/null || echo '')"
if [[ -z "$HEALTH" ]]; then
  bad "api             not answering on :8000"
  note "bash .devcontainer/start.sh   then   tail -20 /tmp/backend.log"
else
  for dep in database vector_store model; do
    DETAIL="$(printf '%s' "$HEALTH" | python -c "
import json,sys
print(json.load(sys.stdin)['dependencies'].get('$dep','?'))" 2>/dev/null || echo '?')"
    case "$DETAIL" in
      down*|'?') bad "$(printf '%-15s' "$dep")${DETAIL}" ;;
      *)         ok  "$(printf '%-15s' "$dep")${DETAIL}" ;;
    esac
  done
fi

# --- the frontend -----------------------------------------------------------
CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 localhost:3000 2>/dev/null || echo 000)"
if [[ "$CODE" == "200" ]]; then
  # Answering on loopback is not enough. Next binds to localhost unless told
  # otherwise, and a loopback-only listener is invisible to the Codespaces port
  # forwarder -- the terminal says 200 while the browser gets a 502.
  if ss -ltn 2>/dev/null | grep -q "0.0.0.0:3000\|\*:3000\|:::3000"; then
    ok "frontend        HTTP 200, reachable from the browser"
  else
    bad "frontend        HTTP 200 on loopback only -- the browser will get 502"
    note "pkill -f 'next dev'; cd frontend && nohup npm run dev > /tmp/frontend.log 2>&1 &"
  fi
else
  bad "frontend        HTTP ${CODE} on :3000"
  note "cd frontend && nohup npm run dev > /tmp/frontend.log 2>&1 &"
fi

# --- the agent --------------------------------------------------------------
command -v claude >/dev/null && ok "claude code     installed" \
                             || bad "claude code     not on PATH"

echo
if [[ "$FAILED" == "1" ]]; then
  echo "  Something above is wrong. Fix it before you start -- every one of"
  echo "  these breaks later, further from the cause."
  exit 1
fi

cat <<NEXT
  Ready.

  1.  claude
  2.  paste the stage 01 prompt from pipeline/01-shape.md
  3.  work through the six stages in order

  Stopwatch on when you start F1. That number decides the timings.
NEXT
