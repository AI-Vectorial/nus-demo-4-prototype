# M04 Policy Assistant

The application built and extended during **M04 — AI-Native Development Lifecycle**,
AI Practitioner Certificate, NUS AIDF / MUFG.

Staff ask questions about internal policy in plain language; the assistant retrieves
from a fictional policy corpus and answers, citing its sources.

> **This repository is a teaching artefact.** Everything in it is fictional. No MUFG
> data, systems or credentials appear anywhere.

---

## Status — step 1 of 8

A **walking skeleton**. It serves, it is tested, and it deploys through a
human-approved pipeline. It does not yet answer questions.

That order is deliberate: **prove the deployment loop before writing the interesting
code.** If a one-line change can travel branch → PR → CI → approval → merge → live
URL, everything after it is content rather than engineering.

| Step | | Status |
|---|---|---|
| **1** | Repo, devcontainer, CI, Railway — **the deploy loop** | ✅ **done** |
| 2 | `docs/project-brief.md` | next |
| 3 | The RAG application — retrieval, generation, persistence — **built through the pipeline itself** | |
| 4 | `PRD.md` + `design/` written from what exists | |
| 5 | `pipeline/` stage files, `AGENTS.md`, `START-HERE.md` | |
| 6 | `features/feature-1..5.md` | |
| 7 | Reference branch — all five features built | |
| 8 | Cards, runbooks, rehearsal, recording | |

---

## Layout

```
backend/                FastAPI
  app/
    api/                routers
    core/               config, database session          PROTECTED
    ingest/             corpus loading, chunking, embedding   PROTECTED
    retrieve/           vector search                     PROTECTED
    generate/           model call, answer composition    PROTECTED
    features/           ← one module per table
  tests/
    regression/         ours, and it must stay green      PROTECTED
    features/           ← one test file per table

frontend/               Next.js 15 · React 19 · TypeScript
  app/                  app router, layout, global styles PROTECTED
  components/
    features/           ← one component per table
  lib/

ci/                     the four checks
docs/                   project brief, PRD, design decisions
pipeline/               the six stages — prompts, templates, gates    [step 5]
features/               the five feature briefs                        [step 6]
tickets/                written during the lab — the Linear replacement
```

**The split that matters:** everything the application needs in order to *function*
is ours. Everything a table builds is a capability the application is better with and
**fine without** — so an unfinished table breaks nothing.

---

## Run it

In a Codespace, nothing. Both services start automatically:

- **`http://localhost:3000`** — the assistant, your branch, live
- `http://localhost:8000/docs` — the API

Locally:

```bash
# backend
cd backend
python -m venv .venv && .venv/Scripts/activate     # or source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload

# frontend, in another terminal
cd frontend
npm install
npm run dev
```

---

## The four checks

Every push runs these. They are the governance, and they are mechanical — nobody
talks their way past them.

| Check | Asks | Teaches |
|---|---|---|
| **`ci/check_scope.py`** | **Did this diff touch something it may not?** | **M04.3 — permission boundaries** |
| `pytest` | Do the acceptance criteria hold? | M04.2 · M04.4 |
| `bandit` | Any obvious security fault? | M04.4 — review pass 2 |
| `ci/check_licences.py` | May we ship every dependency? | M04.4 — review pass 4 |

Run them the way CI does:

```bash
python ci/check_scope.py
cd backend && pytest -q && bandit -r app/ -ll && ruff check app/ tests/
python ci/check_licences.py
cd frontend && npm run typecheck && npm run lint && npm run build
```

### The scope check is the interesting one

It fails the build when a diff touches `pipeline/`, `.github/`, `ci/`, `AGENTS.md`,
the backend core or the shared frontend shell — or when a table's branch strays
outside the three files that table owns.

M04.3's Demo Brief requires one change that is **genuinely rejected — "checkable,
not narrated."** This is it. An agent already told *no* once by a human during plan
review, reaching for a protected file anyway, gets stopped by a machine.

---

## Deployment

```
branch  ──push──▶  scope ▸ backend ▸ frontend  ──green──▶  pull request
                                                                │
                                                    ┌───────────┴───────────┐
                                                    │   HUMAN APPROVAL      │
                                                    │   release manager     │
                                                    └───────────┬───────────┘
                                                                │ merge to main
                                                          Railway deploys
                                                                │
                                                           smoke test
```

**There is no path from a workspace to Railway.** Deployment is reachable only
through CI, and CI stops at a named human. If a table could deploy from a terminal
the gate would be bypassable — and the gate is the lesson.

**Rollback:** revert the merge commit and push. Railway redeploys the previous
version in roughly ninety seconds.

---

## Required configuration

Set on the repository before the first deploy:

| | Where | What |
|---|---|---|
| `RAILWAY_TOKEN` | Repository **secret** | Railway deploy credential |
| `RAILWAY_BACKEND_SERVICE` | Repository **variable** | Backend service name |
| `RAILWAY_FRONTEND_SERVICE` | Repository **variable** | Frontend service name |
| `API_URL` | Repository **variable** | Public backend URL, for the smoke test |
| `production` environment | Settings → Environments | **With a required reviewer** |
| Branch protection on `main` | Settings → Rules | Require CI green **and** one approving review |

The last two are what make the human gate real. Without them the pipeline still runs,
but anyone can merge.

---

*AI Practitioner Certificate · NUS AIDF / MUFG · CONFIDENTIAL — Chartered Vectorial*
