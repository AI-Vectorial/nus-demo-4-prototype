#!/usr/bin/env bash
#
# Reset one table back to clean, after a dry run.
#
#   ./scripts/reset_table.sh 1          reset table 1
#   ./scripts/reset_table.sh 1 --data   reset the data only, keep the branch
#
# Three things get reset:
#   the Postgres database   dropped and recreated, empty
#   the Qdrant collection   deleted -- the next ingest recreates it, at whatever
#                           dimension that table's embedding model needs
#   the branch              table-N reset to main, work/table-N deleted
#
set -euo pipefail

N="${1:-}"
[[ "$N" =~ ^[1-5]$ ]] || { echo "usage: $0 <1-5> [--data]"; exit 1; }
DATA_ONLY=false
[[ "${2:-}" == "--data" ]] && DATA_ONLY=true

DB="table_${N}"
COLLECTION="policy_passages_table_${N}"

echo "Resetting table ${N}"
echo

# --- Postgres ---------------------------------------------------------------
URL="$(railway variables --service Postgres --json 2>/dev/null \
      | python -c 'import json,sys;print(json.load(sys.stdin).get("DATABASE_PUBLIC_URL",""))')"
if [[ -n "$URL" ]] && command -v psql >/dev/null; then
  psql "$URL" -c "DROP DATABASE IF EXISTS ${DB} WITH (FORCE)" >/dev/null
  psql "$URL" -c "CREATE DATABASE ${DB}" >/dev/null
  echo "  database    ${DB} dropped and recreated"
else
  echo "  database    SKIPPED (need psql and the Postgres service)"
fi

# --- Qdrant -----------------------------------------------------------------
QURL="$(railway variables --service qdrant --json 2>/dev/null \
       | python -c 'import json,sys;d=json.load(sys.stdin);print(d.get("RAILWAY_PUBLIC_DOMAIN",""))')"
QKEY="$(railway variables --service qdrant --json 2>/dev/null \
       | python -c 'import json,sys;print(json.load(sys.stdin).get("QDRANT__SERVICE__API_KEY",""))')"
if [[ -n "$QURL" ]]; then
  CODE="$(curl -s -o /dev/null -w '%{http_code}' -X DELETE \
         "https://${QURL}/collections/${COLLECTION}" -H "api-key: ${QKEY}" --max-time 25)"
  echo "  collection  ${COLLECTION} deleted (HTTP ${CODE})"
else
  echo "  collection  SKIPPED (qdrant has no public domain -- delete from the dashboard)"
fi

# --- Branches ---------------------------------------------------------------
if ! $DATA_ONLY; then
  git fetch origin --quiet
  git push origin --delete "table-${N}/build" 2>/dev/null && \
    echo "  branch      table-${N}/build deleted" || \
    echo "  branch      table-${N}/build did not exist"
  git push origin "origin/main:refs/heads/table-${N}" --force-with-lease 2>/dev/null && \
    echo "  branch      table-${N} reset to main" || \
    echo "  branch      table-${N} NOT reset -- remove the ruleset bypass block first"
else
  echo "  branch      left alone (--data)"
fi

echo
echo "Table ${N} is clean. The next ingest will recreate the collection."
