#!/usr/bin/env bash
#
# Create one Postgres database per table on the shared instance.
#
# A separate database, not a schema. Schemas need search_path set correctly on
# every connection, and a table whose agent writes its own session handling will
# get that wrong. A database is isolated whatever the connection does.
#
set -euo pipefail
TABLES="${TABLES:-1 2 3 4 5 facilitator}"

# A table is a number or "facilitator", the sixth table run at the front of the
# room:  3 -> table-3 / table_3,   facilitator -> facilitator / facilitator
slug() { [[ "$1" =~ ^[0-9]+$ ]] && echo "table-$1" || echo "$1"; }
db()   { local s; s="$(slug "$1")"; echo "${s//-/_}"; }

command -v psql >/dev/null || { echo "psql not found -- install postgresql-client"; exit 1; }

URL="$(railway variables --service Postgres --json 2>/dev/null \
      | python -c 'import json,sys;print(json.load(sys.stdin).get("DATABASE_PUBLIC_URL",""))')"

[[ -n "$URL" ]] || { echo "could not read DATABASE_PUBLIC_URL from the Postgres service"; exit 1; }

for N in $TABLES; do
  DB="$(db "$N")"
  if psql "$URL" -tAc "SELECT 1 FROM pg_database WHERE datname='${DB}'" | grep -q 1; then
    echo "  ${DB}    already exists"
  else
    psql "$URL" -c "CREATE DATABASE ${DB}" >/dev/null
    echo "  ${DB}    created"
  fi
done

echo
echo "Each api-table-N resolves DATABASE_URL against its own DATABASE_NAME."
