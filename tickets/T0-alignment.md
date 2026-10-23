# T0 — Alignment

*Written before any ticket. What the agent believes, so you can correct it while
correcting it is still cheap.*

**Table:** 4
**Branch:** work/table-4
**Written:** 2026-10-23
**Corrected by the team:** Approved as written. No corrections. The D0 / PRD §8 conflict below is still open.
*(the team, not a named person — nobody signs anything today)*

---

## What we are building

A single-page policy assistant for Aldermere Bank staff, backed by a FastAPI service and a Next.js interface.
A staff member asks one policy question in plain language and gets one answer that cites the policy sections it was composed from.
If the indexed corpus cannot support an answer, the product refuses and does not call the model.
The corpus is five fictional Aldermere policy documents in `backend/corpus/`, indexed into Qdrant and stored alongside Postgres records.
Scope is F1–F8 as one increment, released in one pull request; F6, F7 and F8 are cuttable.

## Who it is for, and what breaks without it

Operations and front-office staff who hit a policy question mid-task; without it they interrupt colleagues or act on superseded email.

## The contracts we do not get to change

*From PRD §4–§7. These are fixed. Name them so they are not quietly renegotiated at
build time.*

| | |
|---|---|
| Routes (§2) | `/`, `/history`, `/corpus`, `/corpus/[id]`. No settings page |
| `POST /ask` (§5) | Body `{question, conversation_id}`. Response has `outcome` as explicit `answered` / `refused` / `degraded`, plus `answer`, `citations`, `conversation_id`, `message_id`, `latency_ms` |
| `GET /conversations`, `GET /conversations/{id}` (§5) | Newest first, paginated; `title` is the first user message, truncated |
| `GET /corpus`, `GET /corpus/{id}` (§5) | Documents with sections of `{heading, text}` |
| Data model (§6) | Tables `conversations`, `messages`, `message_citations` exactly as written |
| Vector payload (§7) | Fields `text`, `document_id`, `document_title`, `section`, `version`, `status`, `effective`. Add fields if needed; do not rename |
| Config names (§8) | Environment variable names as listed, including `DATABASE_NAME` and `QDRANT_COLLECTION`, which differ per table and must not be changed |
| Requirement ids (§4) | `REQ-I1..I7`, `REQ-R1..R6`, `REQ-C1..C9`, `REQ-G1..G6`, `REQ-B1..B6`, `REQ-A1..A6`, `REQ-U1..U15` |
| Protected paths | `pipeline/`, `.github/`, `ci/`, `AGENTS.md`, `CLAUDE.md`, `START-HERE.md`, `docs/PRD.md`, `docs/features.md`, `docs/project-brief.md`, `backend/corpus/`, `scripts/`, `docs/table-card.md` |

## Where things live

*The scaffold, in the agent's words. This is the section that stops stages 02–06
re-reading the whole repository.*

| | |
|---|---|
| Backend | `backend/app/`. Entry point `main.py` (FastAPI app, lifespan creates DB, background auto-index). Routers mount in `main.py`; `/ask` router is ours to add. Packages: `api/`, `core/`, `generate/`, `ingest/` (empty), `retrieve/`, `features/` (empty) |
| Frontend | `frontend/`. Next.js 16 app router in `app/` (`page.tsx`, `layout.tsx`, `globals.css`, proxy `api/[...path]/route.ts`). Components `components/` (`Answer`, `Chat`, `Citations`, `Degraded`, `Refusal`). API client `lib/api.ts`, types `lib/types.ts` |
| Corpus | `backend/corpus/`. Five documents (travel v3.1 current and v3.0 superseded, KYC v2.4, retention v4.0, outsourcing v1.8), `MANIFEST.yaml`, `EVALUATION.md` (13 questions), `FICTION-AUDIT.md`. **Protected** |
| Tickets | `tickets/`. Epic `T1.md`, children `T1-F1..F8`, later `T1-plan.md`, `T1-review.md`, `T1-release.md` |
| Configuration | Environment variables, read once in `backend/app/core/config.py`. Defaults are present in that file for several of §8's names (see "Still open") |
| Tests | `backend/tests/`. Fixtures in `conftest.py`; regression suite in `tests/regression/` |
| Pipeline docs | `pipeline/` (protected), templates in `pipeline/templates/` |

## What is already built, and must not be built again

*The single most expensive mistake in a sixty-minute build is writing something
the scaffold already gave you. List it here, by name, so no later stage has to
go looking.*

| | |
|---|---|
| Test fixtures (`conftest.py`) | `client` (FastAPI TestClient on `app.main:app`), `store` (empty `FakeVectorStore`), `loaded_store` (store with three passages), `model` (`FakeModel`), `failing_model` (`FakeModel(fail=True)`), `passages` (three embedded `Passage`s), `sample_corpus` (path to `tests/fixtures/corpus/`) |
| Fixture classes | `tests/fixtures/fake_model.py` → `FakeModel`: `generate`, `embed` (deterministic bag-of-words vectors), `was_called`, raises `ProviderError` on failure. `tests/fixtures/fake_store.py` → `FakeVectorStore`: cosine search with `min_score`, `upsert`, `count`, `health`. Both are fakes only; production code is not in them |
| Given modules | `app/retrieve/store.py`: frozen dataclasses `Passage`, `Hit`, and `VectorStore` protocol (`ensure_ready`, `upsert`, `search`, `count`, `health`). `app/retrieve/__init__.py`: `get_vector_store()`, cached. `app/retrieve/qdrant_store.py`: `QdrantVectorStore` implementing that protocol, the only module importing qdrant_client. `app/generate/client.py` + `__init__.py`: `generate(prompt, system, temperature)`, `embed(texts)` (batched, checks dimensions against config), `health()`, `ProviderError(retryable)`; the only module importing the OpenAI SDK. `app/core/config.py`: `settings` with every §8 name. `app/core/database.py`: `Base`, `session_scope()`, `get_session()`, `ensure_database()` (creates this table's DB at boot), `health()`. `app/api/health.py`: `GET /healthz` router, already mounted. `app/main.py`: app, CORS, lifespan, `GET /`, background `_index_if_empty()` that runs `python -m app.ingest` when the collection is empty |
| What `backend/tests/README.md` says | Use the fixtures; no Qdrant or Postgres or network needed in tests. Refusal test asserts `not model.was_called`. Degraded test uses `failing_model`. Commands: `pytest -q`, `pytest -q -k <name>`. CI runs `pytest -q`, `ruff check`, `bandit -r app/ -ll`, and the licence check |
| Regression suite (already written, must pass) | `test_corpus_integrity.py` (corpus shape, the v3.0/v3.1 disagreement, the inclusive £75, the retention conflict, the escalation note, the silent travel policy). `test_retrieval_contract.py` (only `qdrant_store.py` imports the client; interface has no vendor types; domain types frozen). `test_provider_boundary.py` and `test_health.py` (not yet read in detail) |

**Commands**

| | |
|---|---|
| Tests | `cd backend && pytest -q` |
| Lint | `cd backend && ruff check .` (ruff config: line length 100, py312, rules E F I UP B). Security: `bandit -r app/ -ll` |
| Ingest | `cd backend && python -m app.ingest` — **not yet built; this is F1** |
| Run it | API: `bash .devcontainer/start.sh` starts the API on :8000 and the frontend on :3000 (script not yet read in detail). Frontend alone: `cd frontend && npm run dev`. Frontend checks: `npm run lint`, `npm run typecheck` |
| Readiness | `scripts/quickstart.sh 4` checks branch, key, `/healthz` and frontend |

## Still open — do NOT assume these

*The ten decisions in PRD §10 belong to the team and are answered at stage 02. Listing
them here is how we notice if one gets decided for us.*

- [ ] D0 embedding model and dimensions
- [ ] D1 chunk size and overlap
- [ ] D2 the refusal threshold, and how it was arrived at
- [ ] D3 how many passages to retrieve
- [ ] D4 whether superseded policies are shown, hidden or flagged
- [ ] D5 what a refusal says
- [ ] D6 what happens when two policies conflict
- [ ] D7 how citations are grouped
- [ ] D8 how much conversation a follow-up sees
- [ ] D9 whether a follow-up re-retrieves, and on what text

**Flagged for the team — a conflict, not a decision:**

- **D0 vs PRD §8.** PRD §10 lists D0 (embedding model and dimensions) as the team's. PRD §8 lists `EMBEDDING_MODEL_SLUG=openai/text-embedding-3-small` and `EMBEDDING_DIMENSIONS=1536` as if already fixed, and `backend/app/core/config.py` carries those as defaults. Also `MIN_SCORE` (D2) has a default of `0.35` in config, which PRD §8 leaves blank. We have not used these values. Which is it?
- **Minor.** The comment in `config.py` says "PRD section 9, D0"; D0 is in §10. Not a decision; noted only.

## What we are NOT doing

From `docs/features.md`, in our words:

- Settings page, authentication, users or sessions
- Streaming responses
- Re-ranking, hybrid search or query expansion unless retrieval is measured failing first
- Editing or adding to the corpus. If retrieval is weak we fix retrieval
- F9 to F12 (feedback, personal-data guardrail, audit export, answer confidence) until F1–F8 is merged and deployed
- Anything outside the corpus: no web search, no general knowledge

---

> **Read this file at the start of every later stage.** It is shorter than the PRD and
> it is the thing that has already been corrected by a human.
