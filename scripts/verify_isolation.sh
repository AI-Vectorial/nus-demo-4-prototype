#!/usr/bin/env bash
#
# Prove the tables are isolated BEFORE the room arrives.
#
# Isolation you assume is not isolation. This indexes into table 1 and asserts
# that every other table's passage count is unchanged -- the single check that
# matters most, because five agents will be writing storage code at once.
#
set -euo pipefail
TABLES="${TABLES:-1 2 3 4 5}"

echo "Reading passage counts from each table's /healthz"
declare -A BEFORE
for N in $TABLES; do
  URL="$(railway variables --service "api-table-${N}" --json 2>/dev/null \
        | python -c 'import json,sys;print(json.load(sys.stdin).get("RAILWAY_PUBLIC_DOMAIN",""))')"
  [[ -n "$URL" ]] || { echo "  table ${N}: no public domain yet -- skipping"; continue; }
  BEFORE[$N]="$(curl -s --max-time 20 "https://${URL}/healthz" \
               | python -c 'import json,sys;print(json.load(sys.stdin)["dependencies"]["vector_store"])' 2>/dev/null || echo unknown)"
  echo "  table ${N}: ${BEFORE[$N]}"
done

cat <<'NEXT'

Now, by hand:
  1. Run ingestion on table 1 only
  2. Re-run this script
  3. Table 1's count must change. Every other count must NOT.

If any other count moved, the tables are sharing a collection and the lab
cannot run until that is fixed.
NEXT
