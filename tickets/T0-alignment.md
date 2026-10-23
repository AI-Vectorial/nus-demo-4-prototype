# T0 — Alignment

*Written before any ticket. What the agent believes, so you can correct it while
correcting it is still cheap.*

**Table:** 1
**Branch:** work/table-1
**Written:** 2026-10-23 08:23 UTC
**Corrected by the team:** Reviewed and approved as written (2026-10-23).
*(the team, not a named person — nobody signs anything today)*

---

## What we are building

Aldermere Bank staff need quick answers to policy questions while doing their work.
The assistant searches only the approved policy corpus and cites the sections it uses.
It refuses when the corpus cannot support an answer; the model does not decide whether
an answer is safe to give.
The target is one product increment covering F1–F8, delivered through the six stages.
F6, F7 and F8 may be cut for time, but a cut feature must disappear from the interface.

## Who it is for, and what breaks without it

Operations and front-office staff need policy answers without interrupting colleagues
or searching through outdated files and email.
Without a current, traceable source, staff may act on a superseded or unsupported answer.

## The contracts we do not get to change

*From PRD §4–§7. These are fixed. Name them so they are not quietly renegotiated at
build time.*

| | |
|---|---|
| Requirements | PRD §4 defines the F1–F8 requirements for ingestion, retrieval, conversations, generation, browsing, API and UI. Keep their behaviors and identifiers intact. |
| Routes and API | PRD §2 fixes `/`, `/history`, `/corpus`, `/corpus/[id]`; §5 defines `POST /ask` and the conversation and corpus GET routes. |
| Ask response | Preserve the §5 fields and meanings: outcome, answer, citations, conversation id, message id and latency; refusal has no citations, degraded has passages but no composed answer. |
| Data model | §6 fixes `conversations`, `messages` and `message_citations`, their UUID keys, relationships, timestamps and recorded answer metadata. |
| Vector payload | §7 names `text`, `document_id`, `document_title`, `section`, `version`, `status` and `effective`; add fields if needed, but do not rename these. |
| Existing frontend types | `frontend/lib/types.ts` currently uses `exchange_id` and omits some §5 fields. The PRD contract is authoritative; this mismatch is a scaffold note, not a contract change. |

## Where things live

*The scaffold, in the agent's words. This is the section that stops stages 02–06
re-reading the whole repository.*

| | |
|---|---|
| Backend | FastAPI service and modules are in `backend/app/`; regression and feature tests are in `backend/tests/`. |
| Frontend | Next.js app is in `frontend/app/`, with reusable UI in `frontend/components/` and API/types in `frontend/lib/`; the home screen is currently a scaffold. |
| Corpus | Five policy documents and supporting files are in `backend/corpus/`. This is protected input, not a place to improve retrieval by editing content. |
| Tickets | Stage records belong in `tickets/`; templates are under `pipeline/templates/`. |
| Configuration | Backend settings are read in `backend/app/core/config.py`; examples are `backend/.env.example` and `frontend/.env.example`. Runtime values come from environment variables. |

## What is already built, and must not be built again

*The single most expensive mistake in a sixty-minute build is writing something
the scaffold already gave you. List it here, by name, so no later stage has to
go looking.*

| | |
|---|---|
| Test fixtures (`conftest.py`) | `client` (FastAPI `TestClient`), `store` (empty in-memory store), `loaded_store` (three preloaded passages), `model` (network-free fake), `failing_model` (fake provider failure), `passages` (three embedded sample passages), and `sample_corpus` (fixture corpus path). |
| Given modules | Backend: `app.main`, `app.api.health`, `app.core.config`, `app.core.database`, `app.generate`/`app.generate.client`, and `app.retrieve`/`app.retrieve.store`/`app.retrieve.qdrant_store`; `app.ingest` and `app.features` are empty packages. Tests: `tests.test_fixtures_work` and `tests.regression.test_corpus_integrity`, `test_health`, `test_provider_boundary`, `test_retrieval_contract`; doubles: `tests.fixtures.fake_model` and `tests.fixtures.fake_store`. Frontend scaffold: `app/page.tsx`, `app/api/[...path]/route.ts`, components `Answer`, `Chat`, `Citations`, `Degraded`, `Refusal`, and `lib/api.ts`/`lib/types.ts`. |
| What `backend/tests/README.md` says | The seven fixtures need no Postgres, Qdrant or network; use them for response, retrieval, refusal and degraded-mode tests. In particular, assert refusal does not call generation and use `failing_model` to test provider failure. |

**Commands**

| | |
|---|---|
| Tests | `cd backend && pytest -q` (all tests); `cd backend && pytest -q tests/test_ingest.py` (one file, when added). |
| Lint | `cd backend && ruff check app/ tests/` (the CI lint command). |
| Ingest | `cd backend && python -m app.ingest` (the required F1 entry point; not implemented in this scaffold yet; `--force` is also required). |
| Run it | `bash .devcontainer/start.sh` starts the local API and frontend; use `http://localhost:8000/docs` for the API and `http://localhost:3000` for the UI. |

## Still open — do NOT assume these

*The ten decisions in PRD §10 belong to the team and are answered at stage 02. Listing
them here is how we notice if one gets decided for us.*

- [ ] D0 — Embedding model and dimensions
- [ ] D1 — Chunk size and whether chunks overlap
- [ ] D2 — Refusal threshold and how it is determined
- [ ] D3 — Number of passages to retrieve
- [ ] D4 — Whether superseded policies are shown, hidden or flagged
- [ ] D5 — Refusal wording
- [ ] D6 — Handling conflicting policies
- [ ] D7 — How citations are grouped
- [ ] D8 — How much conversation a follow-up sees
- [ ] D9 — Whether a follow-up re-retrieves, and what text is embedded

> **A value appearing in the plan that is not answered above is a finding.** Raise it
> at the gate. Starter configuration defaults are not team decisions.

## What we are NOT doing

No settings page, authentication, streaming, policy editing or exception decisions;
no answers from outside the corpus and no automatic re-indexing on document changes.
Re-ranking, hybrid search and query expansion are also out unless retrieval is measured
to be failing; do not edit the protected corpus to compensate.

---

> **Read this file at the start of every later stage.** It is shorter than the PRD and
> it is the thing that has already been corrected by a human.
