#!/usr/bin/env bash
#
# Provision the M04 lab on Railway: five tables, each with their own API and
# web service, sharing one Postgres instance and one Qdrant instance.
#
#   Postgres   one instance, five databases      table_1 .. table_5
#   qdrant     one instance, five collections    policy_passages_table_N
#   api-table-N / web-table-N                    one pair per table
#
# Isolation is injected here, not configured by a table. A table cannot reach
# another table's data because it is never given the address of it.
#
# Idempotent: re-running adds what is missing and leaves the rest alone.
#
#   ./scripts/provision_railway.sh            provision everything
#   ./scripts/provision_railway.sh --dry-run  print what it would do
#
set -euo pipefail

PROJECT="${RAILWAY_PROJECT:-nus-module-4}"
TABLES="${TABLES:-1 2 3 4 5}"
DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

run() {
  if $DRY_RUN; then printf '  would run: %s\n' "$*"; else "$@"; fi
}

say()  { printf '\n\033[1m%s\033[0m\n' "$*"; }
note() { printf '  %s\n' "$*"; }

# -----------------------------------------------------------------------------
say "M04 Railway provisioning -- project: $PROJECT"
$DRY_RUN && note "(dry run: nothing will change)"

command -v railway >/dev/null || { echo "railway CLI not found"; exit 1; }
railway whoami >/dev/null 2>&1 || { echo "not logged in -- run: railway login"; exit 1; }

run railway link --project "$PROJECT" >/dev/null 2>&1 || true

existing_services() {
  railway status --json 2>/dev/null \
    | python -c "import json,sys;d=json.load(sys.stdin);[print(e['node']['name']) for e in d.get('services',{}).get('edges',[])]" \
    2>/dev/null || true
}

SERVICES="$(existing_services)"
has_service() { echo "$SERVICES" | grep -qx "$1"; }

# -----------------------------------------------------------------------------
say "1. Shared data services"

if has_service "Postgres"; then
  note "Postgres            already exists"
else
  note "Postgres            creating"
  run railway add --database postgres
fi

if has_service "qdrant"; then
  note "qdrant              already exists"
else
  note "qdrant              creating"
  run railway add --service qdrant --image qdrant/qdrant
  # Qdrant is only reachable on the private network, but an unauthenticated
  # vector store is still an unauthenticated vector store.
  QKEY="$(python -c 'import secrets;print(secrets.token_urlsafe(32))')"
  run railway variables --service qdrant --set "QDRANT__SERVICE__API_KEY=$QKEY"
  run railway variables --service qdrant --set "QDRANT__STORAGE__STORAGE_PATH=/qdrant/storage"
fi

# -----------------------------------------------------------------------------
say "2. Per-table services"

for N in $TABLES; do
  for KIND in api web; do
    SVC="${KIND}-table-${N}"
    if has_service "$SVC"; then
      note "$SVC        already exists"
    else
      note "$SVC        creating"
      run railway add --service "$SVC"
    fi
  done
done

# -----------------------------------------------------------------------------
say "3. Wiring -- each table sees only its own database and collection"

for N in $TABLES; do
  API="api-table-${N}"
  WEB="web-table-${N}"

  # The backend reaches Postgres and Qdrant over Railway's private network.
  # DATABASE_URL points at this table's OWN database, not the default one.
  run railway variables --service "$API" \
    --set "DATABASE_URL=\${{Postgres.DATABASE_URL}}" \
    --set "DATABASE_NAME=table_${N}" \
    --set "QDRANT_URL=http://\${{qdrant.RAILWAY_PRIVATE_DOMAIN}}:6333" \
    --set "QDRANT_API_KEY=\${{qdrant.QDRANT__SERVICE__API_KEY}}" \
    --set "QDRANT_COLLECTION=policy_passages_table_${N}" \
    --set "TABLE_ID=${N}"

  # The browser calls the API directly, so it needs the public address and the
  # API needs to allow that origin.
  run railway variables --service "$WEB" \
    --set "API_URL=https://\${{${API}.RAILWAY_PUBLIC_DOMAIN}}" \
    --set "TABLE_ID=${N}"

  run railway variables --service "$API" \
    --set "ALLOWED_ORIGINS=https://\${{${WEB}.RAILWAY_PUBLIC_DOMAIN}}"

  note "table ${N}             db=table_${N}  collection=policy_passages_table_${N}"
done

# -----------------------------------------------------------------------------
say "4. Public domains"

for N in $TABLES; do
  for KIND in api web; do
    run railway domain --service "${KIND}-table-${N}" >/dev/null 2>&1 || true
  done
  note "table ${N}             domains requested"
done

# -----------------------------------------------------------------------------
say "Done."
cat <<'NEXT'

  Still to do by hand -- these need a credential we do not put in a script:

    1. Create the five databases on the Postgres instance:
         ./scripts/create_databases.sh

    2. Set the OpenRouter key on each api-table-N service:
         railway variables --service api-table-N --set "OPENROUTER_API_KEY=..."

    3. Confirm isolation before the lab:
         ./scripts/verify_isolation.sh

NEXT
