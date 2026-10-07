# Table N — your card

**One page. Print five, write the number in.**

---

## You are table N

| | |
|---|---|
| **Your branch** | `table-N` — you work on `work/table-N` |
| **Your app** | `https://web-table-N-production.up.railway.app` |
| **Your API** | `https://api-table-N-production.up.railway.app` |
| **Target to compare against** | `https://nus-module-4-web-production.up.railway.app` |

**Everything is already configured.** Your API key, your database and your
vector store are running in your Codespace. You set up nothing.

---

## First five minutes

```bash
claude                            # or: codex
```

**Your agent creates `work/table-N` itself** — stage 01's first instruction.
You do not need to.

**First prompt — do not ask it to build anything yet:**

```
Read AGENTS.md, then docs/project-brief.md, docs/PRD.md and docs/features.md.
Summarise in five lines what we are building. Do not write any code.
```

Then open **`pipeline/01-shape.md`** and follow it.

---

## The six stages — follow them in order

```
01 shape ──▶ 02 plan ──▶ 03 build ──▶ 04 review ──▶ 05 release ──▶ 06 verify
  15min        20min        60min        20min        10min        15min
                 │                                                    │
          ⚠️ HUMAN GATE                                        ⚠️ HUMAN GATE
```

**At stage 02 an instructor will ask you why.** Be able to answer:

- Why that chunk size?
- Why that refusal threshold — and how did you arrive at it?
- What happens when two policies contradict each other?

> *"The agent chose it"* is a failed answer. **Your plan can be rejected.**

---

## Done means

> **Six stages completed and something deployed to your URL.
> Not a finished chatbot.**

You are **building** the whole product — F1 to F8, in one pull request at stage
05, deployed at stage 06. You are **marked** on the six stages.

**Short on time? Cut scope, never a stage.** Cut F8, then F7, then F6 — and take
the button out of the top bar with the feature. The bar only shows what exists.

---

## Three things that will fail your build

| | |
|---|---|
| Editing `docs/`, `pipeline/`, `ci/`, `.github/`, **`backend/corpus/`** | CI refuses it |
| Pushing straight to `table-N` | PR only, and it needs an approval |
| Letting your agent decide a PRD §10 question | It is yours, and you will be asked |

> **The corpus is the temptation.** When retrieval performs badly, editing a
> policy so it contains your search words makes the demo work and the product
> worthless. **Fix retrieval.**

---

## Useful commands

```bash
cd backend && python -m app.ingest    # index the corpus (after F1)
pytest -q                             # your acceptance criteria
curl localhost:8000/healthz           # what is up, what is down
```

**Stuck for ten minutes? Ask an instructor.** That is what they are for.

---

*Policy Assistant · M04 · Aldermere Bank is fictional*
