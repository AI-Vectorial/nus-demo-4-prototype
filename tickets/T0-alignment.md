# T0 — Alignment

*Written before any ticket. What the agent believes, so you can correct it while
correcting it is still cheap.*

**Table:** 1
**Branch:** work/table-1
**Written:** 2026-10-15
**Corrected by:** MSV (reviewed; no corrections recorded in this file)

---

## What we are building

A single-page policy assistant for Aldermere Bank staff: one question in, one answer out, with
the policy sections it was composed from shown beside it. If the corpus cannot support an
answer, the product refuses and says where to go instead, and it never calls the model in that
case. Retrieval is the deterministic core; the model only writes the answer from passages it was
handed, and the product must still work as a plain policy search when the model is switched off.
The increment is F1–F8 in one pull request, with F6, F7 and F8 cuttable, and deployment is last.

## Who it is for, and what breaks without it

Operations and front-office staff who hit a policy question mid-task (about 1,400 people). Without
it they keep interrupting colleagues or acting on stale email, and roughly one answer in six cites
a superseded policy, which the audit only finds later.

## The contracts we do not get to change

*From PRD §4–§7. These are fixed. Name them so they are not quietly renegotiated at build time.*

| | |
|---|---|
| Routes | `POST /ask`; `GET /conversations?limit=`; `GET /conversations/{id}`; `GET /corpus`; `GET /corpus/{id}`; `GET /healthz`. UI routes: `/`, `/history`, `/corpus`, `/corpus/[id]` |
| Ask response | `outcome` is explicit and one of `answered` / `refused` / `degraded`. Refusal carries `answer` = the reason and where to go, and `citations` = `[]`. Degraded carries `answer` = `null` and the passages found. Each citation has `document_id`, `document_title`, `section`, `version`, `status` (`current`/`superseded`), `score` |
| Data model | Tables `conversations`, `messages` (role, content, outcome, model, prompt_version, latency_ms), `message_citations`. `messages` is both the record and the follow-up context |
| Vector payload | `text`, `document_id`, `document_title`, `section`, `version`, `status`, `effective`. Names may be extended, not renamed |
| Configuration | Environment variables with the names in PRD §8 (`LLM_MODEL`, `EMBEDDING_MODEL_SLUG`, `DATABASE_NAME=table_N`, `QDRANT_COLLECTION=policy_passages_table_N`, `CONTEXT_MESSAGES=5`, `GENERATION_ENABLED`, etc.). No model name, URL, dimension or threshold as a literal in code |
| Refusal type | Retrieval returns grounded passages *or* an explicit insufficiency — never an ambiguous empty list (REQ-R3) |
| Protected paths | `pipeline/`, `.github/`, `ci/`, `AGENTS.md`, `CLAUDE.md`, `START-HERE.md`, `docs/PRD.md`, `docs/features.md`, `docs/project-brief.md`, `backend/corpus/`, `scripts/`, `docs/table-card.md`. Nothing in them changes |
| Dependencies | Licence-checked in CI; GPL/LGPL/AGPL/MPL refused. Any new package is asked about first |

## Where things live

*The scaffold, in the agent's words. This is the section that stops stages 02–06
re-reading the whole repository.*

| | |
|---|---|
| Backend | `backend/app/`: `main.py` (FastAPI app, mounts routers), `api/health.py` (`/healthz`, only router so far), `core/config.py` (all settings from env), `core/database.py` (SQLAlchemy/pg8000, creates this table's DB on boot). Empty packages to fill: `ingest/` (F1), `retrieve/` (F2/F3; `store.py` holds the `Passage`/`Hit`/`VectorStore` interface and `qdrant_store.py` is the only Qdrant importer), `generate/` (F4; `client.py` is the only OpenRouter/SDK importer, with `generate()`, `embed()`, `health()`), `features/` (F6–F8). `app/__init__.py` files are empty |
| Frontend | `frontend/app/` (`layout.tsx`, `page.tsx`, `globals.css`, catch-all proxy `api/[...path]/route.ts`), `frontend/components/` (`Answer`, `Chat`, `Citations`, `Degraded`, `Refusal` — shells, to be filled), `frontend/lib/api.ts` and `lib/types.ts` (typed client, given). Next.js, TypeScript, ESLint |
| Corpus | `backend/corpus/`: five documents (`travel-expense-policy-v3.1.md` current, `travel-expense-policy-v3.0.md` superseded, `client-onboarding-kyc-v2.4.md`, `records-retention-v4.0.md`, `outsourcing-third-party-v1.8.md`), plus `MANIFEST.yaml` and `EVALUATION.md` (13 questions: Q1–Q10 answerable, Q11–Q13 must refuse). **Protected, read-only** |
| Tests | `backend/tests/`: `conftest.py` (fixtures `client`, `store`, `loaded_store`, `model`, `failing_model`, `passages`, `sample_corpus`); `fixtures/` (fake model, fake store, small corpus); `regression/` (corpus integrity, health, provider boundary, retrieval contract) — these must stay green. `features/` and `test_fixtures_work.py` are ours to extend |
| Tickets | `tickets/` (ours). `README.md` describes the epic and child layout |
| Pipeline | `pipeline/` and `docs/` — read, not edited |
| Configuration | `backend/app/core/config.py` (reads env once); `backend/.env.example` for local values. In the Codespace, keys are already in the environment — never paste them into a file |
| Deploy | Railway, one service for the API (`backend/Dockerfile`) and one for the frontend (`frontend/Dockerfile`). Nothing deploys before stage 05 |

**Commands**

| | |
|---|---|
| Tests | `cd backend && pytest -q` |
| Lint | `cd backend && ruff check app/ tests/`; `cd frontend && npm run lint` |
| Security | `cd backend && bandit -r app/ -ll` |
| Licence | `python ci/check_licences.py` |
| Scope | `python ci/check_scope.py` |
| Frontend checks | `cd frontend && npm run build && npm run typecheck` |
| Ingest | `cd backend && python -m app.ingest` — **does not exist yet; F1 builds it** |
| Run API | `cd backend && uvicorn app.main:app --reload` (Codespace: port 8000; `curl localhost:8000/healthz`) |
| Run UI | `cd frontend && npm run dev` (port 3000, bound to `0.0.0.0`) |
| Readiness | `./scripts/quickstart.sh 1` — checks branch, key, stores, frontend |

## Findings from reading the scaffold

These are not decisions. They are values already sitting in the scaffold that touch PRD §10, and
they go to the plan gate as questions, not as settled choices.

- `backend/app/core/config.py` ships `MIN_SCORE` defaulting to `0.35` (D2). That is a number before
  anyone has tuned it against `EVALUATION.md`.
- `config.py` ships `EMBEDDING_DIMENSIONS` defaulting to `1536` (D0). The Qdrant collection is fixed
  at whatever dimension is first indexed.
- `CHUNK_MAX_TOKENS`, `CHUNK_OVERLAP_TOKENS`, `RETRIEVE_TOP_K` are named in PRD §8 but absent from
  `config.py`. They are D1 and D3 and are not yet added.
- `backend/app/main.py` has a placeholder comment for `ask.router` that does not exist yet.

## Still open — do NOT assume these

*The ten decisions in PRD §10 belong to the team and are answered at stage 02. Listing
them here is how we notice if one gets decided for us.*

- [ ] D0 Embedding model and dimensions — **unanswered** (scaffold default 1536 noted above)
- [ ] D1 Chunk size, and whether chunks overlap — **unanswered**
- [ ] D2 Refusal threshold, and how it was arrived at — **unanswered** (scaffold default 0.35 noted above)
- [ ] D3 How many passages to retrieve — **unanswered**
- [ ] D4 Whether superseded policies are shown, hidden or flagged — **unanswered**
- [ ] D5 What a refusal says — **unanswered**
- [ ] D6 What happens when two policies conflict — **unanswered**
- [ ] D7 How citations are grouped — **unanswered**
- [ ] D8 How much conversation a follow-up sees — **unanswered**
- [ ] D9 Whether a follow-up re-retrieves, and on what text — **unanswered**

> **A value appearing in the plan that is not answered above is a finding.** Raise it
> at the gate.

## What we are NOT doing

From `docs/features.md` "What not to build", in our words:

- No settings page — configuration is environment variables only.
- No authentication, users or sessions.
- No streaming responses.
- No re-ranking, hybrid search or query expansion unless retrieval is measurably failing.
- No editing or authoring of the corpus, and no changes to protected paths to make a retrieval
  result look better. If retrieval is weak, we fix retrieval.
- No re-indexing triggered by document change; ingestion is a command we run.
- No answering from anything outside the corpus, and no decisions about whether an exception is
  permitted.
- Beyond the critical path (F9–F12: feedback, personal-data guardrail, audit export, answer
  confidence) — only after F1–F8 are merged.

---

> **Read this file at the start of every later stage.** It is shorter than the PRD and
> it is the thing that has already been corrected by a human.
