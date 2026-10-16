#!/usr/bin/env bash
#
# Keep this Codespace to its own table's branches.
#
# AGENTS.md asks an agent to read only its own branch. This makes it true
# rather than requested: the remote-tracking refs for every other branch are
# removed, so `git show origin/reference:...` fails with "unknown revision"
# instead of printing somebody's answers, and `git branch -r` lists one branch.
#
# It matters because the interesting part of five tables building one
# specification is where they differ. An agent that read another table's work
# has not produced a second result -- it has produced a copy, and afterwards
# nobody can tell which.
#
# Only table-N is tracked, not work/table-N: the work branch does not exist on
# the remote until stage 05 pushes it, and naming a missing ref makes every
# later `git fetch` fail with "couldn't find remote ref". Push is unaffected --
# set-branches governs fetch only, and `git push -u` still sets up tracking.
#
# NEVER fatal. A Codespace that fails to open is a far worse outcome than one
# that can see a branch it should not.

set +e

_branch="$(git branch --show-current 2>/dev/null)"
_table="$(printf '%s' "${_branch}" | grep -oE 'table-[1-5]|facilitator' | head -1)"

if [ -z "${_table}" ]; then
  echo "  branch '${_branch}' names no table -- leaving remote refs alone"
  exit 0
fi

# Future fetches bring back this branch and nothing else.
git remote set-branches origin "${_table}" 2>/dev/null || true

# Remove the ones the clone already brought down.
git branch -r --format='%(refname:short)' 2>/dev/null \
  | grep -v -x "origin/${_table}" \
  | grep -v -x "origin/work/${_table}" \
  | while read -r _ref; do
      [ -n "${_ref}" ] && git branch -rd "${_ref}" >/dev/null 2>&1
    done
git remote set-head origin -d >/dev/null 2>&1 || true

echo "  this Codespace tracks ${_table} only -- $(git branch -r 2>/dev/null | wc -l) remote branch(es) visible"
exit 0
