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
# rate limits and the spend separate.
#
# OPENROUTER_API_KEY set directly still wins, so one shared key works for a dry
# run before five exist.

if [ -z "${OPENROUTER_API_KEY:-}" ]; then
  _repo="${CODESPACE_VSCODE_FOLDER:-/workspaces/nus-demo-4-prototype}"
  _branch="$(git -C "$_repo" branch --show-current 2>/dev/null || echo '')"
  _table="$(printf '%s' "$_branch" | grep -oE 'table-[1-5]' | head -1 | tr -d 'table-')"

  if [ -n "$_table" ]; then
    _var="OPENROUTER_API_KEY_TABLE_${_table}"
    eval "_key=\${${_var}:-}"
    if [ -n "$_key" ]; then
      export OPENROUTER_API_KEY="$_key"
      export TABLE_ID="$_table"
    else
      echo "  !! ${_var} is not set. Branch is '${_branch}'."
      echo "  !! Tell an instructor. Do NOT paste a key into a file."
    fi
    unset _var _key
  elif [ -n "$_branch" ]; then
    echo "  !! No OpenRouter key, and branch '${_branch}' does not name a table."
    echo "  !! Expected something like 'work/table-3'."
  fi
  unset _repo _branch _table
fi
