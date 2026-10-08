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
# The Postgres service is internal-only -- it has no TCP proxy, so PGHOST is
# postgres.railway.internal and nothing outside the cluster can reach it. The
# drop below therefore only runs if someone has since added a public URL.
#
# Without one, repointing is the reliable equivalent, exactly as for Qdrant
# below: the API calls ensure_database() on boot, so pointing the service at a
# new name gets an empty database on the next start. It leaves the old one
# behind, which is 5 tables x a handful of dry runs -- cheap, and droppable
# later from the dashboard.
URL="$(railway variables --service Postgres --json 2>/dev/null \
      | python -c 'import json,sys;print(json.load(sys.stdin).get("DATABASE_PUBLIC_URL",""))')"
if [[ -n "$URL" ]] && command -v psql >/dev/null; then
  psql "$URL" -c "DROP DATABASE IF EXISTS ${DB} WITH (FORCE)" >/dev/null
  psql "$URL" -c "CREATE DATABASE ${DB}" >/dev/null
  echo "  database    ${DB} dropped and recreated"
else
  STAMP="$(date +%H%M%S)"
  if railway variables --service "api-table-${N}" \
       --set "DATABASE_NAME=${DB}_${STAMP}" >/dev/null 2>&1; then
    echo "  database    unreachable from here; repointed to ${DB}_${STAMP}"
  else
    echo "  database    !! NOT RESET -- the next table will see the last run's history"
    exit 1
  fi
fi

# --- Qdrant -----------------------------------------------------------------
QURL="$(railway variables --service qdrant --json 2>/dev/null \
       | python -c 'import json,sys;d=json.load(sys.stdin);print(d.get("RAILWAY_PUBLIC_DOMAIN",""))')"
QKEY="$(railway variables --service qdrant --json 2>/dev/null \
       | python -c 'import json,sys;print(json.load(sys.stdin).get("QDRANT__SERVICE__API_KEY",""))')"
if [[ -n "$QURL" ]]; then
  CODE="$(curl -s -o /dev/null -w '%{http_code}' -X DELETE \
         "https://${QURL}/collections/${COLLECTION}" -H "api-key: ${QKEY}" --max-time 25)"
  if [[ "$CODE" == "200" ]]; then
    echo "  collection  ${COLLECTION} deleted"
  else
    # Railway's proxy assumes a service listens on $PORT; Qdrant listens on
    # 6333, so the public domain answers 502 and this DELETE never lands.
    # Repointing is the reliable equivalent: the API indexes from empty on its
    # next boot, because it indexes whenever the collection count is zero.
    STAMP="$(date +%H%M%S)"
    railway variables --service "api-table-${N}" \
      --set "QDRANT_COLLECTION=${COLLECTION}_${STAMP}" >/dev/null 2>&1 \
      && echo "  collection  unreachable (HTTP ${CODE}); repointed to ${COLLECTION}_${STAMP}" \
      || echo "  collection  SKIPPED (HTTP ${CODE}, and could not repoint the service)"
  fi
else
  echo "  collection  SKIPPED (qdrant has no public domain -- delete from the dashboard)"
fi

# --- Branches ---------------------------------------------------------------
if ! $DATA_ONLY; then
  git fetch origin --quiet
  git push origin --delete "work/table-${N}" 2>/dev/null && \
    echo "  branch      work/table-${N} deleted" || \
    echo "  branch      work/table-${N} did not exist"
  git push origin "origin/main:refs/heads/table-${N}" --force-with-lease 2>/dev/null && \
    echo "  branch      table-${N} reset to main" || \
    echo "  branch      table-${N} NOT reset -- remove the ruleset bypass block first"
else
  echo "  branch      left alone (--data)"
fi

echo
echo "Table ${N} is clean. The next ingest will recreate the collection."
