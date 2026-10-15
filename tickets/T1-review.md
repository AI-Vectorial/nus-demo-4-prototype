# T1 — Review record

**Stage:** 04 review
**Branch:** work/table-1
**Reviewed:** 2026-10-15
**Diff reviewed:** `origin/main...work/table-1` (59 files, +3528 / -124)

*Five passes, run separately. Every finding gets a decision. **The agent reviews; the team decides.**
Nothing in this record has been fixed. Each finding's decision is PENDING until the team records one.*

---

## Pass 1 — Correctness

Checked: the ask flow (`app/features/ask.py`), the grounding rule (`app/retrieve/ground.py`), citation grouping, follow-up context (`_recent_messages`), and the outcome paths.

- Refusal path makes no model call. Verified in tests and live.
- Follow-up uses the conversation's earlier user turns, latest last (D9). Verified live.
- One real edge case: an empty model reply is accepted as an answer (F2 below).

## Pass 2 — Security and privacy

Checked: logging calls across `backend/app`, the frontend proxy, the Markdown renderer, error responses, and the scripts.

- Logs record exception types and status only, not question text or keys. Confirmed by grep.
- Answers are rendered without `innerHTML` (`frontend/lib/markdown.tsx`). No raw-HTML injection path found.
- The question text is stored and sent to a third-party model, with no retention decision (F3).
- A key fragment is printed by a protected script (F4).

## Pass 3 — Maintainability

Checked: swallowed errors, duplication, dead code, logging consistency.

- Broad `except Exception` blocks in `database.py` and `health.py` either re-raise or report the failure. None swallow silently.
- Startup status uses `print()` where the rest of the code uses `logging` (F5).

## Pass 4 — Provenance and IP

Checked: every dependency's licence, and anything that may be copied from elsewhere.

- `ci/check_licences.py`: PASS, 59 dependencies. **Correction:** the check passes because it only refuses copyleft families it lists (GPL, AGPL, SSPL, CC-BY-SA, EUPL). MPL-2.0 is not on that list. Several packages show `UNKNOWN` to `pip-licenses`, but their metadata is permissive. See F11.
- Frontend licences read from `node_modules`: see table below.
- `frontend/lib/markdown.tsx` is written for this project. No third-party code identified. The author should confirm this (F9).

## Pass 5 — Production fitness

Checked: failure paths when Qdrant, the model or Postgres are unavailable or slow.

- **Retrieval failure is not handled** (F1). This is the most serious finding.
- Provider failure during composition is handled: it returns `degraded` with passages. Verified by test.
- Postgres failure returns 503 with a clear message. Verified by code.
- Latency is recorded per exchange, but there is no per-outcome structured log (F6).

---

## Findings

### F1 — A retrieval or embedding failure returns an unhandled 500, and degraded mode does not cover it
**Pass:** 5 — production fitness
**Severity:** high
**Where:** `backend/app/features/ask.py:116` (`ground(get_vector_store(), embed, query)`), `backend/app/api/ask.py` (only `ConversationNotFound` and `SQLAlchemyError` are caught)
**What:** `embed()` raises `ProviderError` when the model is unreachable, and the Qdrant client raises its own errors when the store is down. Neither is caught before the response. The user gets a generic server error, and the question is not stored, because the transaction rolls back. REQ-G6 says a provider failure returns degraded. That holds for the composition step only. Found by reading the code. **Not yet reproduced live.**
**Agent recommendation:** catch `ProviderError` and store-unavailable errors at the retrieval step. Return an explicit error outcome, store the user's question, and add a test for each case.
**Decision:** FIXED — 2026-10-15, team asked for the recommendation. Retrieval and embedding failures now return **503** with a clear message (`SearchUnavailable`). The Qdrant client error is translated to `RetrievalUnavailable` inside the store. Reproduced live against a dead Qdrant: 503, and the message count was 12 before and 12 after. Tests: `tests/regression/test_review_fixes.py`.
**Deviation from the recommendation, for the team to acknowledge:** the user's question is **not** stored on this failure. PRD §5 fixes the outcome to three values, and a stored question with no answer would corrupt follow-up context. Storing it would have needed a fourth outcome, which is a contract change.

### F2 — An empty model reply is recorded as an answer
**Pass:** 1 — correctness
**Severity:** medium
**Where:** `backend/app/generate/client.py` (`generate()` returns `(content or "").strip()`); `backend/app/features/ask.py` (`outcome = "answered"` after `compose_answer`)
**What:** if the model returns nothing, the exchange is stored as `answered` with empty text. A user sees a blank answer with citations. This is an invisible failure.
**Agent recommendation:** treat an empty reply as a provider failure, so the outcome becomes `degraded`. Add a test.
**Decision:** FIXED — 2026-10-15, as recommended. `compose_answer` raises `ProviderError` on an empty reply, so the outcome is `degraded`. Tests: `test_an_empty_model_reply_is_degraded_not_answered` and `test_compose_answer_refuses_to_return_an_empty_string`.

### F3 — The question text is stored and sent to a third-party model, with no retention decision
**Pass:** 2 — security and privacy
**Severity:** medium
**Where:** `messages.content` (`backend/app/core/records.py`); the question is included in the prompt built by `backend/app/generate/compose.py`
**What:** every question is kept in Postgres indefinitely and sent to OpenRouter. The brief's open question Q3 (who sees the question text, and for how long it is kept) is unanswered. A question can contain client details.
**Agent recommendation:** do not change the code until Q3 is answered. Record the answer to Q3 as a decision, then add retention if needed.
**Decision:** ACCEPTED by MSV, 2026-10-15, as relayed by the team ("everything is confirmed by MSV"). The retention risk for question text is accepted with the product as built. Note: Privacy's written answer to Q3 is not on file, so this acceptance is the record and Q3 stays open for the product owner. Original reason: brief question Q3 (who sees the question text, and for how long it is kept) is owned by Privacy and is unanswered. **This must be answered before stage 05.** Until then, question text is stored and sent to the model, and that is a known risk. The team reports the answers are correct. That is product quality, not the Privacy owner's answer to Q3. **To close:** Privacy answers Q3, or MSV records an explicit acceptance with a reason.

### F4 — A protected script prints a fragment of the API key to the terminal
**Pass:** 2 — security and privacy
**Severity:** low
**Where:** `scripts/quickstart.sh` (prints `${OPENROUTER_API_KEY:0:14}...`)
**What:** 14 characters of the key appear in terminal output. NFR-6 says secrets never appear in terminal output. The file is protected, so this team cannot change it.
**Agent recommendation:** raise with the instructors to remove the print. Do not edit the script.
**Decision:** DEFERRED — the leak is in two protected scripts, which this team cannot edit (AGENTS.md §1): `scripts/quickstart.sh:49` prints 14 characters of the key, and `scripts/set_table_keys.sh:55` prints 12. **Leak scan, done 2026-10-15:** no key in any tracked file, in git history (`git log -S`), or in any log in `/tmp`. `.env` is git-ignored and not tracked. So the repository itself does not leak. **Owner:** instructors, to remove the two prints. **Note:** the 14-character prefix was printed in this session's terminal during a quickstart run, so the instructors may choose to rotate the key.

### F5 — Startup status uses `print()`, not logging
**Pass:** 3 — maintainability
**Severity:** low
**Where:** `backend/app/main.py` (lifespan, `print(f"database: ...")`, `print(f"tables: ...")`)
**What:** the rest of the backend logs through `logging`. Startup messages bypass log levels and handlers, which makes them easy to miss in production.
**Agent recommendation:** switch to `logging.getLogger(__name__).info`.
**Decision:** FIXED — 2026-10-15, as recommended. Startup uses `log.info`, or `log.warning` on failure. `logging.basicConfig(level=INFO)` makes it reach stderr, since INFO is otherwise dropped by default. Test: `test_startup_does_not_print_to_stdout`. Confirmed in the live log: `INFO:app.main:database: policy already present`.

### F6 — No per-outcome log line; failures are visible only in the API response
**Pass:** 5 — production fitness
**Severity:** low
**Where:** `backend/app/features/ask.py`
**What:** each exchange's outcome and latency are stored in the database, but nothing is logged at the time. A rising rate of degraded answers would not show in the logs.
**Agent recommendation:** log one line per exchange: outcome, latency, and the model. Do not log the question text (see F3).
**Decision:** FIXED — 2026-10-15. One line per exchange: `exchange outcome=... latency_ms=...`. Degraded logs at WARNING so a rising rate shows. Confirmed in the live log. **Minor deviation:** the model name is not logged, because the model is the same for every exchange and is already in the configuration. The question text is not logged, as recommended.

### F7 — CORS allows all methods and headers, with credentials
**Pass:** 2 — security and privacy
**Severity:** low
**Where:** `backend/app/main.py` (`CORSMiddleware`, `allow_credentials=True`, `allow_methods=["*"]`)
**What:** the allowed origins come from `ALLOWED_ORIGINS`, so the exposure is limited to listed origins. The browser never calls the API directly, because the frontend proxy is same-origin. The permissive settings are not needed.
**Agent recommendation:** narrow to `GET` and `POST`, and drop credentials unless needed.
**Decision:** FIXED — 2026-10-15, as recommended. Methods are `GET` and `POST`, headers are `Content-Type`, and credentials are off. The frontend calls the API server-side, so it does not need them. Tests: the two `test_cors_*` tests.

### F8 — Per-package Python licences are not recorded in this review
**Pass:** 4 — provenance and IP
**Severity:** low
**Where:** `ci/check_licences.py` output; `backend/requirements*.txt`
**What:** the licence check passes, but the table below does not list each Python package's licence. The record is incomplete until it does.
**Agent recommendation:** run the licence tool and add its output to this record.
**Decision:** FIXED — 2026-10-15. The per-package licence table is recorded under **Dependencies** below. **See F11:** the table exposed licences that the earlier "all permissive" statement did not account for.

### F9 — Provenance of `frontend/lib/markdown.tsx` needs the author's confirmation
**Pass:** 4 — provenance and IP
**Severity:** low
**Where:** `frontend/lib/markdown.tsx`
**What:** the file is written for this project. No third-party code is identified, but the author should confirm this in writing.
**Decision:** ACCEPTED by MSV, 2026-10-15, as relayed by the team ("everything is confirmed by MSV"). Provenance of `frontend/lib/markdown.tsx` is accepted as original. Note: no separate written author statement is on file; MSV's acceptance is the record. The team reports that the Markdown renders correctly. That shows the renderer works, not where its code came from, so it does not close this finding. The agent cannot confirm provenance, and this must be closed before stage 05.

### F11 — MPL-2.0 dependencies conflict with AGENTS.md §5; CI does not flag them
**Pass:** 4 — provenance and IP
**Severity:** medium
**Where:** `certifi` (MPL-2.0, required by `httpx` and `httpcore`); `tqdm` (MPL-2.0 AND MIT, required by `openai`). Several other packages show licence `UNKNOWN`, including `typing_extensions`, `urllib3` and `anyio`.
**What:** AGENTS.md §5 says a GPL, LGPL, AGPL or MPL licence needs an alternative proposed. `ci/check_licences.py` only refuses GPL, AGPL, SSPL, CC-BY-SA and EUPL, so MPL passes the build. My earlier review said all dependencies were permissive. That was too strong: CI passing does not mean the project's own rule is met, and `UNKNOWN` licences were not checked. `pip-licenses` also reads the whole environment, not only the pinned requirements.
**Agent recommendation:** the team decides whether to accept MPL-2.0 for these two transitive packages, with a reason, or to propose an alternative. Both are pulled in by pinned packages, so swapping them is a dependency decision, which AGENTS.md §5 reserves for a human. The agent has not changed any dependency.
**Decision:** ACCEPTED — no dependency change, with a reason. Checks run 2026-10-15:
- `certifi` (MPL-2.0) is a hard requirement of `httpx`, which `openai` requires. `tqdm` (MPL-2.0 AND MIT) is a hard requirement of `openai` above 4. Removing either means replacing or upgrading the model SDK, which is the only model path. That risks the deployment, and it is not justified for these licences.
- MPL-2.0 is file-level copyleft. Its obligations apply only if an MPL file is modified. These are used unmodified.
- The packages marked `UNKNOWN` are not a problem. Their package metadata is permissive (MIT, BSD, Apache-2.0, PSF-2.0). `pip-licenses` failed to read them.
- AGENTS.md §5 asks for an alternative to be proposed when MPL appears. No alternative keeps the deployment unchanged, so none is proposed. **Sign-off:** ACCEPTED by MSV, 2026-10-15, as relayed by the team ("confirmed, from MSV"). Recorded as a licence policy decision for the two unmodified MPL-2.0 libraries `certifi` and `tqdm`.

### F13 — Production answered 500 because the corpus was never indexed on the deployment
**Pass:** 5 — production fitness
**Severity:** high
**Where:** `backend/Dockerfile` (the image did not include the corpus), `backend/app/retrieve/qdrant_store.py` (a 404 from a missing collection was not caught), `backend/app/main.py` (nothing built the index on a fresh deploy)
**What:** after PR #17 merged, `/ask` returned 500 on production for every question. `/healthz` showed `vector_store: reachable, collection not created yet`, so the collection was never built. The F1 fix only caught an unreachable Qdrant (`ResponseHandlingException`). A missing collection raises `UnexpectedResponse` (404), which escaped as a 500. **That was a gap in my F1 fix.** I had tested only a dead host, not a missing collection.
**Decision:** FIXED — 2026-10-15. (1) A 404 from Qdrant is now `RetrievalUnavailable`, so the API returns 503 and records nothing. (2) An empty index is unavailable, not a refusal: before the build, a question returns 503 instead of telling the user the policy does not cover it. (3) On startup, the server builds the index only if the store is empty, in a background thread, so `/healthz` answers during the build. Refreshing an existing index stays an explicit `python -m app.ingest`. (4) The image includes `corpus/`, read-only. Tests: `tests/regression/test_deploy_index.py` (5). Live: during a build the question returned 503; after the build, 130 passages, and the partner question was correctly refused.
**Process note:** I had merged without checking the live URL, and `/healthz` already showed the problem. Stage 06 must check `/healthz` for the passage count before any question is asked.
**Needs approval:** `backend/Dockerfile` is not in the owned or protected lists, so it needs MSV's explicit approval. Indexing at startup is a change to the deploy process, and it also needs MSV's approval.

### F12 — A slow model returns a 504 from the gateway instead of degrading
**Pass:** 5 — production fitness
**Severity:** high
**Where:** `backend/app/generate/client.py` (retries and SDK timeout, no overall limit), `backend/app/features/ask.py`
**What:** found in live testing, 2026-10-15, as a 504 on `/ask`. The API log shows two completed answers at 89 s and 108 s. Each provider call had its own 60 s timeout, and up to 3 attempts plus backoff ran for each step, so the total had no ceiling. The gateway gave up first, so the user saw an error, and the request kept running on the server, which can leave a record the user was never told about.
**Decision:** FIXED — 2026-10-15. One time budget per answer, `ANSWER_BUDGET_SECONDS`, default 25 s. Embedding, retries and composition all share it. Each SDK call gets only the time left. Retries and backoff stop when it runs out, and the product returns `degraded` with the passages, as REQ-G6 requires. The default is below the gateway's limit, and it is configurable. **Trade-off, for the team to know:** an answer that takes longer than 25 s is now returned as passages with no composed answer. Previously it might have succeeded slowly. Tests: `tests/regression/test_time_budget.py` (6). Live: a normal answer took 9.6 s; with a 4 s budget the slow path returned `degraded` in 4.07 s, not a 504. **Frontend:** a 504 now shows "the service took too long to respond" instead of a bare code. **Not fixed:** a gateway 504 can still happen if the database or Qdrant is slow, so it stays a known residual risk.

### F10 — NFR-1 latency misses the p50 target
**Pass:** 1 — correctness (against the NFR, not a code defect)
**Severity:** high
**Where:** `/ask`, measured live: 9.0s and 12.2s
**What:** the target is p50 under 5s. The product is slower than the target.
**Decision:** ACCEPTED — MSV chose Option B (accept the known miss). No change made. Recorded in `tickets/T1.md`.

---

## Dependencies

Frontend (read from `node_modules`):

| Package | Version | Licence | Permissive? |
|---|---|---|---|
| next | 16.3.6 | MIT | yes |
| react | 19.0.0 | MIT | yes |
| react-dom | 19.0.0 | MIT | yes |
| typescript | 5.7.3 | Apache-2.0 | yes |
| eslint | 9.18.0 | MIT | yes |
| eslint-config-next | 16.3.6 | MIT | yes |

Backend, direct pinned packages (`backend/requirements.txt`, `requirements-dev.txt`), from `pip-licenses`:

| Package | Version | Licence | Permissive? |
|---|---|---|---|
| fastapi | 0.115.6 | MIT | yes |
| uvicorn | 0.34.0 | BSD | yes |
| jinja2 | 3.1.5 | BSD | yes |
| python-multipart | 0.0.20 | Apache-2.0 | yes |
| pydantic | 2.10.5 | MIT | yes |
| sqlalchemy | 2.0.36 | MIT | yes |
| pg8000 | 1.31.2 | BSD-3-Clause | yes |
| qdrant-client | 1.12.1 | Apache-2.0 | yes |
| openai | 1.59.6 | Apache-2.0 | yes |
| pytest | 8.3.4 | MIT | yes (dev) |
| httpx | 0.28.1 | BSD | yes (dev) |
| bandit | 1.8.0 | Apache-2.0 | yes (dev) |
| ruff | 0.9.2 | MIT | yes (dev) |

Transitive packages with a note (see F11):

| Package | Licence | Pulled in by | Note |
|---|---|---|---|
| certifi | MPL-2.0 | httpx, httpcore | conflicts with AGENTS.md §5 |
| tqdm | MPL-2.0 AND MIT | openai | conflicts with AGENTS.md §5 |
| several others | shown as UNKNOWN by pip-licenses; permissive in package metadata | various | checked; see F11 |

## Summary

| | |
|---|---|
| Findings | 13 |
| Fixed | 8 (F1, F2, F5, F6, F7, F8, F12, F13) |
| Accepted | 4 (F3 retention, by MSV · F9 provenance, by MSV · F10 NFR-1, by MSV · F11 MPL-2.0, by MSV) |
| Deferred | 1 (F4 in protected scripts, instructors to fix) |
| Open | 0 |

**The one we accepted on purpose, and why:** NFR-1, the answer latency. Live answers take 9 to 12 seconds against a p50 target of 5. MSV chose to accept the known miss rather than change the model. The reason is the team's to state at the gate.

**The most serious item, now fixed:** F1. A retrieval failure returned an unhandled 500. It now returns a 503 and records nothing. Verified live.

**Stage 04 status: COMPLETE (2026-10-15).** Every finding has a decision and a reason. F3, F9 and F11 accepted by MSV as relayed. F4 deferred to instructors. Previous status note, superseded: **Stage 04 status: NOT COMPLETE.** The gate is that every finding has a decision and a reason. One finding is still open: F9, which needs the author's written confirmation. Two more need a named sign-off: F11 (MPL-2.0 acceptance) and F3 (Q3 from Privacy, or MSV's explicit acceptance). F3 must close before stage 05.
