# Policy Assistant

**You are going to build this, and deploy it.**

A staff member at Aldermere Bank asks a policy question in plain language. The assistant
finds the relevant passages in the bank's policy corpus, answers **only from those
passages**, and shows which sections it used. When the corpus cannot support an answer,
**it says so and stops.**

Built during **M04 — AI-Native Development Lifecycle**, AI Practitioner Certificate,
NUS AIDF / MUFG.

> **This repository is a teaching artefact.** Aldermere Bank is fictional. Every policy,
> figure and name in it is invented. No MUFG data, systems or credentials appear anywhere.

---

## 👉 Start with [`START-HERE.md`](START-HERE.md)

Ninety seconds. It tells you where you are, what to read, and which file to open first.

---

## What you are building

Five tables. **Five separate builds of the same specification, deployed to five separate
URLs.** Your table owns a branch, a database, a vector collection and a pair of
deployments. Nothing you do can affect another table.

```
F1 ingest ──▶ F2 retrieve ──▶ F3 refuse ──▶ F4 generate ──▶ F5 ask + UI ──▶ DEPLOY
                                                                   │
                                            F6 follow-up ◀─────────┘
                                            F7 corpus browser
```

| | |
|---|---|
| [`docs/project-brief.md`](docs/project-brief.md) | **why** this product exists, and whether AI belongs in it |
| [`docs/PRD.md`](docs/PRD.md) | **what must be true.** The contract — routes, data model, payload |
| [`docs/features.md`](docs/features.md) | **what to build first** |

> **PRD §10 is the one to read twice.** Ten decisions are deliberately left to you —
> chunk size, the refusal threshold, what happens when two policies contradict each other.
> **You will be asked to defend your answers**, and *"the agent chose it"* is a failed
> answer.

---

## The six stages

```
01 shape ──▶ 02 plan ──▶ 03 build ──▶ 04 review ──▶ 05 release ──▶ 06 verify
  15min        25min        60min        25min         10min        15min
                 │                                                     │
          ⚠️ HUMAN GATE                                        ⚠️ HUMAN GATE
       your plan is approved                                  your release is
            or rejected                                     approved, then merges
```

Each stage in [`pipeline/`](pipeline/) says what to give your agent, what it produces, and
what has to be true before you move on. **Start at [`pipeline/01-shape.md`](pipeline/01-shape.md).**

> **Done is a completed pipeline and a deployed increment — not a finished product.**
>
> A team that ships ingestion and retrieval but runs out of time before generation has
> still shaped a ticket, defended a plan, reviewed in five passes, written a rollback and
> released through a gate. **That is the module.** If you are running short, **cut scope,
> never a stage.**

---

## The stack

| | |
|---|---|
| **FastAPI** · Python 3.12 | the API |
| **React** via Next.js · TypeScript | the interface |
| **Postgres** | conversations and their turns |
| **Qdrant** | the embedded policy passages |
| **OpenRouter** | every model call — chat and embeddings |
| **Railway** | your deployment |
| **GitHub Actions** | the four checks, and the gate |

---

## Layout

```
backend/                FastAPI
  corpus/               the Aldermere policy documents        PROTECTED
    MANIFEST.yaml         what is in the corpus, and why
    EVALUATION.md         13 questions -- 10 answerable, 3 not
  app/
    api/                your routers
    core/               config, database session
    ingest/             ← F1  loading, chunking, embedding
    retrieve/           ← F2/F3  search, and the refusal rule
      store.py            Passage, Hit, the VectorStore interface  (given)
      qdrant_store.py     the only module importing the Qdrant client  (given)
    generate/           ← F4  the prompt, the composed answer
      client.py           the only module importing the model SDK  (given)
  tests/
    conftest.py           fixtures: fake store, fake model, sample corpus  (given)
    regression/           ours, and it must stay green

frontend/               React / Next.js
  app/                  routes: / and /corpus
  components/           Answer, Citations, Refusal, Degraded  (shells, yours to fill)
  lib/                  typed API client and shared types  (given)

pipeline/               the six stages                        PROTECTED
docs/                   brief, PRD, feature list              PROTECTED
ci/                     the four checks                       PROTECTED
tickets/                yours -- written as you go
```

---

## Run it

**In a Codespace, nothing.** Both services start automatically, and your API key is
already in your environment.

- **`http://localhost:3000`** — the assistant, your branch, live
- `http://localhost:8000/docs` — the API

Locally:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate    # or .venv/Scripts/activate
pip install -r requirements-dev.txt
cp .env.example .env                                  # then fill it in
uvicorn app.main:app --reload

cd frontend && npm install && npm run dev
```

Index the corpus once you have built F1:

```bash
cd backend && python -m app.ingest
```

---

## The four checks

Every push runs these. They are the governance, and they are mechanical — nobody talks
their way past them.

| Check | Asks | Teaches |
|---|---|---|
| **`ci/check_scope.py`** | **Did this change touch something it may not?** | **M04.3 — permission boundaries** |
| `pytest` | Do the acceptance criteria hold? | M04.2 · M04.4 |
| `bandit` | Any obvious security fault? | M04.4 — review pass 2 |
| `ci/check_licences.py` | May we ship every dependency? | M04.4 — review pass 4 |

Run them the way CI does:

```bash
python ci/check_scope.py
cd backend && pytest -q && bandit -r app/ -ll && ruff check app/ tests/
python ci/check_licences.py
cd frontend && npm run build && npm run typecheck && npm run lint
```

> **The licence check is not paperwork.** It already refused a build on this project:
> `psycopg` is LGPLv3 and arrived as a side effect of adding Postgres. Nobody was looking
> for it.

### What you may not change

```
pipeline/    .github/    ci/    AGENTS.md    START-HERE.md
docs/PRD.md  docs/features.md   docs/project-brief.md
backend/corpus/    scripts/    docs/instructor/
```

**`backend/corpus/` is the one you will be tempted by.** When retrieval performs badly,
editing a policy document so it contains the words you searched for makes the demo work
and the product worthless. **Fix retrieval.**

---

## How your work ships

```
work on work/table-N
        │  push -- CI runs the checks, nothing deploys
        ▼
open PR:  work/table-N ──▶ table-N
        │
        ▼
CI: scope ▸ backend ▸ frontend ▸ gate
        │
┌───────┴───────────────┐
│   HUMAN APPROVAL      │   ← the release manager
└───────┬───────────────┘
        │ merge to table-N
        ▼
CI deploys ──▶ api-table-N + web-table-N
        ▼
smoke test on your own URL
```

**A push never deploys.** Only a merge into `table-N` does, and that merge needs an
approval. If a push could deploy, the gate would be bypassable — and the gate is the
module.

**Rollback:** revert the merge commit and push. Railway redeploys the previous version in
about ninety seconds.

**If a deploy fails, your live site is unaffected.** Railway does not route traffic to a
build whose health check never passed, so the previous version keeps serving.

---

## Your data is yours

One Postgres instance and one Qdrant instance, partitioned per table:

| | |
|---|---|
| `DATABASE_NAME=table_N` | your own database, not a schema |
| `QDRANT_COLLECTION=policy_passages_table_N` | your own collection |

**Both are set for you.** You cannot reach another table's data, and re-indexing yours
affects nobody else.

---

## If something breaks

| | |
|---|---|
| Tests failing | `cd backend && pytest -q` — read the failure before changing anything |
| API unreachable | `curl localhost:8000/healthz` — it reports every dependency |
| CI red | Click **Details** on the check. The message says what and why |
| Scope check red | Your agent edited a protected file. **Revert it** — do not argue with it |
| Deploy red | Your live site is fine. Check the Railway build logs, then `/healthz` |
| Stuck ten minutes | **Ask an instructor.** That is what they are there for |

---

*AI Practitioner Certificate · NUS AIDF / MUFG · Aldermere Bank is fictional · CONFIDENTIAL — Chartered Vectorial*
