# Credentials — where everything lives

**A table never sees, types, pastes or commits a secret.** Three stores, none of
which is a file anyone touches.

---

## The three stores

| Where | What | Used by |
|---|---|---|
| **GitHub → Secrets → Actions** | `RAILWAY_TOKEN` | CI, to deploy |
| **GitHub → Secrets → Codespaces** | `OPENROUTER_API_KEY_TABLE_1` … `_5` | their dev environment |
| **Railway → per service** | `OPENROUTER_API_KEY`, `DATABASE_URL`, `QDRANT_*` | the deployed app |

---

## How the key reaches a Codespace

Codespaces secrets are **repository-wide**, so all five land in every Codespace.
`.devcontainer/start.sh` selects the one matching the checked-out branch:

```
work/table-3  ──▶  OPENROUTER_API_KEY_TABLE_3  ──▶  OPENROUTER_API_KEY
```

If `OPENROUTER_API_KEY` is already set, that wins — so **one shared key works for
a dry run** before five separate ones exist.

**If the right secret is missing**, `start.sh` says so loudly and names the
variable it expected. It does not fail silently, and it does not tell anyone to
paste a key anywhere.

---

## ⚠️ Current state — one key, not five

All five Codespaces secrets currently hold **the same key**, so a dry run works
today. **Before delivery, replace them with five separate keys.**

**Why it matters:** five tables embedding a corpus at the same moment on one key
is the most likely way to stall the whole room at once. Separate keys mean one
table can be rate-limited without taking the other four down — and you get
per-table cost attribution.

### To switch to five

1. OpenRouter → Keys → create five, named `m04-table-1` … `m04-table-5`
2. **Set a spend cap on each.** Five agents in a loop burn budget fast, and
   `gpt-oss-120b` being cheap is not the same as being free
3. Then:

```bash
for N in 1 2 3 4 5; do
  gh secret set "OPENROUTER_API_KEY_TABLE_$N" --app codespaces --body "<key $N>"
  railway variables --service "api-table-$N" --set "OPENROUTER_API_KEY=<key $N>"
done
```

Both places, same key per table — otherwise cost attribution is meaningless.

---

## What a table is told

One line, in `START-HERE.md`:

> *Your API key is already in your environment. You do not need to configure
> anything.*

**That is the whole briefing.** If a table is reading about credentials,
something has gone wrong.

---

## Rotating a key

1. OpenRouter → revoke the old one, create a replacement
2. Update the Codespaces secret **and** the Railway variable
3. Existing Codespaces need a rebuild to pick it up; Railway redeploys on its own

---

## Pre-flight

- [ ] `RAILWAY_TOKEN` in **Actions** secrets
- [ ] Five keys in **Codespaces** secrets — ⚠️ **five distinct keys, not one**
- [ ] A spend cap on every key
- [ ] Each `api-table-N` carries its own key
- [ ] `start.sh` selection verified **in a real Codespace**, on a `work/table-N` branch
- [ ] ⚠️ **No participant has admin on the repository** — admins bypass the branch ruleset, and that bypass is what lets an instructor reset a table
- [ ] No key in any file, log or terminal output

---

*M04 · Instructor material · not for participants*
