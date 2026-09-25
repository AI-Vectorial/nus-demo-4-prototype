#!/usr/bin/env bash
#
# Create the five table branches and the ruleset that makes the gate real.
#
#   table-N          the table's production branch. Deploys to api/web-table-N
#   work/table-N    where they work. No protection -- they push here freely
#
# The ruleset covers table-* and NOT table-*/build, so a team can push their
# work as often as they like and still cannot reach their own production branch
# without a pull request and a human.
#
set -euo pipefail

REPO="${REPO:-AI-Vectorial/nus-demo-4-prototype}"
TABLES="${TABLES:-1 2 3 4 5}"

command -v gh >/dev/null || { echo "gh CLI not found"; exit 1; }

echo "1. Branches"
MAIN_SHA="$(gh api "repos/${REPO}/git/ref/heads/main" --jq .object.sha)"
for N in $TABLES; do
  if gh api "repos/${REPO}/git/ref/heads/table-${N}" >/dev/null 2>&1; then
    echo "   table-${N}    already exists"
  else
    gh api -X POST "repos/${REPO}/git/refs" \
      -f "ref=refs/heads/table-${N}" -f "sha=${MAIN_SHA}" >/dev/null
    echo "   table-${N}    created at main"
  fi
done

echo
echo "2. Ruleset on table-*"

# An admin bypass is retained deliberately. It is what lets an instructor reset
# a table between dry runs. It does NOT weaken the gate, because participants
# are given WRITE access, never admin -- so for them the rule is absolute.
#
# The pre-flight check is therefore "no participant has admin", which is a
# stronger control than removing the bypass and hoping nobody needs it at 17:15.
cat > /tmp/table-ruleset.json <<'JSON'
{
  "name": "table protection",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": { "include": ["refs/heads/table-1","refs/heads/table-2","refs/heads/table-3","refs/heads/table-4","refs/heads/table-5"], "exclude": [] }
  },
  "bypass_actors": [
    { "actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always" }
  ],
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    { "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false,
        "automatic_copilot_code_review_enabled": false,
        "allowed_merge_methods": ["squash","merge"]
      } },
    { "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": false,
        "do_not_enforce_on_create": false,
        "required_status_checks": [{ "context": "gate" }]
      } }
  ]
}
JSON

EXISTING="$(gh api "repos/${REPO}/rulesets" --jq '.[] | select(.name=="table protection") | .id' 2>/dev/null || true)"
if [[ -n "$EXISTING" ]]; then
  gh api -X PUT "repos/${REPO}/rulesets/${EXISTING}" --input /tmp/table-ruleset.json --jq '"   updated: " + .name'
else
  gh api -X POST "repos/${REPO}/rulesets" --input /tmp/table-ruleset.json --jq '"   created: " + .name'
fi
rm -f /tmp/table-ruleset.json

echo
echo "3. What this means"
cat <<'NEXT'
   work/table-N   push freely. CI runs the checks. No deploy.
   table-N         pull request only. gate green + 1 approval. Then it deploys.

   Admin bypass retained so a table can be reset between dry runs.
   PRE-FLIGHT: confirm no participant has admin on this repo.
NEXT
