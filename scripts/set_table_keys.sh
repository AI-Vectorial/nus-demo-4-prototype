#!/usr/bin/env bash
#
# Load five distinct OpenRouter keys into both places that need them.
#
# Create the keys first, in the OpenRouter dashboard, with a SPEND CAP on each:
#   https://openrouter.ai/keys   ->  m04-table-1 .. m04-table-5
#
# Then:
#   ./scripts/set_table_keys.sh keys.txt
#
# keys.txt is five lines, table 1 first, nothing else. DELETE IT AFTERWARDS --
# the script reminds you.
#
# Five keys rather than one is about isolation, not capacity: measured at 20
# concurrent generations a single key handled it without a failure. What five
# buys is that one table hitting a limit cannot stall the other four, and that
# spend is attributable per table.
#
set -euo pipefail

FILE="${1:-}"
[[ -f "$FILE" ]] || { echo "usage: $0 <file with five keys, one per line>"; exit 1; }

mapfile -t KEYS < "$FILE"
[[ ${#KEYS[@]} -eq 5 ]] || { echo "expected 5 keys, found ${#KEYS[@]}"; exit 1; }

seen=$(printf '%s\n' "${KEYS[@]}" | sort -u | wc -l)
if [[ "$seen" -ne 5 ]]; then
  echo "!! only $seen distinct keys. Five identical keys give none of the isolation"
  echo "!! this exists for. Aborting."
  exit 1
fi

for i in "${!KEYS[@]}"; do
  N=$((i + 1))
  KEY="${KEYS[$i]}"
  [[ -n "$KEY" ]] || { echo "key $N is blank"; exit 1; }

  gh secret set "OPENROUTER_API_KEY_TABLE_${N}" --app codespaces --body "$KEY" >/dev/null
  echo "  table ${N}  codespaces secret set"

  railway variables --service "api-table-${N}" --set "OPENROUTER_API_KEY=${KEY}" >/dev/null 2>&1
  echo "  table ${N}  railway variable set"
done

cat <<'NEXT'

  Done. Two things left:

    1. DELETE the key file you just used.
    2. An OPEN Codespace will not see a changed secret until it is rebuilt:
       Command Palette -> Codespaces: Rebuild Container.

  Verify a Codespace picked the right one, from inside it:
       echo "${OPENROUTER_API_KEY:0:12}..."
    and check it differs between two tables.
NEXT
