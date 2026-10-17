#!/usr/bin/env bash
#
# Put this table's OpenRouter key in the environment.
#
# Sourced from ~/.bashrc, so EVERY terminal has it -- not just the one that
# started the servers. That distinction cost us a real bug: start.sh exported
# the key and launched uvicorn, so the API worked, but a table opening a fresh
# terminal to run `python -m app.ingest` had no key at all. The server looked
# healthy while the first thing anyone builds could not run.
#
# Secrets are repository-wide, so all five land in every Codespace. This picks
# the one belonging to whichever table's branch is checked out, which keeps the
# rate limits and the spend separate. The facilitator's branches (facilitator,
# work/facilitator) use OPENROUTER_API_KEY_FACILITATOR.
#
# OPENROUTER_API_KEY set directly still wins, so one shared key works for a dry
# run before five exist.

if [ -z "${OPENROUTER_API_KEY:-}" ]; then
  _repo="${CODESPACE_VSCODE_FOLDER:-/workspaces/nus-demo-4-prototype}"
  _branch="$(git -C "$_repo" branch --show-current 2>/dev/null || echo '')"
  _table="$(printf '%s' "$_branch" | grep -oE 'table-[1-5]' | head -1 | tr -d 'table-')"
  case "$_branch" in facilitator|work/facilitator) _table="facilitator" ;; esac

  if [ -n "$_table" ]; then
    _var="OPENROUTER_API_KEY_TABLE_${_table}"
    [ "$_table" = "facilitator" ] && _var="OPENROUTER_API_KEY_FACILITATOR"
    eval "_key=\${${_var}:-}"
    if [ -n "$_key" ]; then
      export OPENROUTER_API_KEY="$_key"
      export TABLE_ID="$_table"
    else
      # Say which of the two failures this is. They look identical from here
      # and they are fixed in completely different places, which has already
      # cost one afternoon.
      # wc -l, not grep -c: grep exits 1 when there are no matches, so a
      # `|| echo 0` fallback fires as well and the count arrives doubled.
      _seen="$(env | grep '^OPENROUTER_API_KEY' 2>/dev/null | wc -l | tr -d ' ')"
      echo "  !! ${_var} is not set. Branch is '${_branch}'."
      if [ "${_seen}" = "0" ]; then
        echo "  !! No OPENROUTER_* variable reached this container at all."
        echo "  !! For an instructor: the secrets are not crossing into the"
        echo "  !! dev container. Check devcontainer.json remoteEnv, and that"
        echo "  !! this account has WRITE access -- GitHub withholds secrets"
        echo "  !! from codespaces whose user cannot write to the repo."
      else
        echo "  !! ${_seen} other OPENROUTER_* variable(s) ARE present, so"
        echo "  !! secrets do reach this container -- ${_var} itself is"
        echo "  !! missing or misnamed in the repository's Codespaces secrets."
      fi
      echo "  !! Tell an instructor. Do NOT paste a key into a file."
      unset _seen
    fi
    unset _var _key
  elif [ -n "$_branch" ]; then
    echo "  !! No OpenRouter key, and branch '${_branch}' does not name a table."
    echo "  !! Expected something like 'work/table-3' or 'work/facilitator'."
  fi
  unset _repo _branch _table
fi
