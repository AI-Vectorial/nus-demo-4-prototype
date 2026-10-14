# T1 — Review record

**Stage:** 04 review
**Branch:** work/table-3
**Reviewed:** 2026-10-08, the diff from `0c6b95f` (table-3 at branch time) to the end of stage 03

*Five passes, run separately. Every finding gets a decision.*

**Who decided.** The project owner gave a standing instruction on 2026-10-08: fix legitimate
findings, and stop only for a product or governance decision the existing decisions, PRD
and AGENTS.md cannot settle. So the agent made the FIXED decisions below. Every ACCEPTED or
DEFERRED finding either rests on a decision the team already made (cited) or is flagged
**for the release gate**, where a human approves the merge.

---

## Pass 1 — Correctness

Read against T1's criteria and the PRD contracts. Boundaries: blank input, empty model
output, a missing or stale index, a reopened degraded turn, and the follow-up window at its
edge (tested at 5 messages).

Findings: **R1, R2, R3, R4, R5.**

## Pass 2 — Security and privacy

Where the question text goes:

- Postgres `messages.content` (required for history)
- the embedding and chat calls to OpenRouter
- **never** the application log: `test_c22_the_question_is_never_logged`, plus the live
  log checked by hand

Errors are logged as type names only, and responses carry generic text. Model output is
rendered by react-markdown with no raw HTML and its default URL sanitising, so model or
corpus text has no script path. All SQL goes through the ORM. No secrets in code, config
examples or logs.

Findings: **S1, S2.**

## Pass 3 — Maintainability

Duplication, dead code, swallowed errors, and whether a stranger could follow it. Each
broad `except` is commented and reports what it caught (`/healthz`, the index status,
`StoreUnavailable`). None is silent.

Findings: **M1, M2, M3, M4, M5, M6.**

## Pass 4 — Provenance and IP

Python dependencies are unchanged by T1. The frontend gains the two packages the team
approved at stage 02, which bring in 98 new packages, all MIT (97) or ISC (1). No code was
copied from elsewhere. The prompts and the refusal text were written for this project.

Findings: **P1.**

## Pass 5 — Production fitness

Tried live:

- Qdrant down
- Postgres down
- both down
- generation off (`GENERATION_ENABLED=false`)
- a provider failure (fake)
- a fresh service with no index

Then asked how the deployed service gets its index at all.

Findings: **F1, F2, F3, F4, F5, F6.**

---

## Findings

### R1 — A blank question was searched
**Pass:** 1 · **Severity:** low · **Where:** `backend/app/api/ask.py` (`AskRequest`)
**What:** `"   "` passed `min_length=1`. It was embedded and searched, then refused.
**Decision:** FIXED — whitespace is stripped and a blank question is a 422. Test:
`test_a_blank_question_is_rejected`.

### R2 — An empty model reply was shown as an empty answer
**Pass:** 1 · **Severity:** low · **Where:** `backend/app/generate/answer.py` (`compose`)
**What:** `outcome: answered` with no text. The user saw a blank answer box above the
citations.
**Decision:** FIXED — an empty reply degrades: passages, no answer. Test:
`test_an_empty_reply_degrades_rather_than_showing_nothing`.

### R3 — A degraded turn reopened from History shows sections, not passage text
**Pass:** 1 · **Severity:** low · **Where:** `frontend/app/page.tsx`, PRD §6
**What:** passage text travels in the live response but is not stored. `message_citations`
is the fixed §6 model and has no text column.
**Decision:** ACCEPTED — §6 is a fixed contract. Each section still links to its full text
in the corpus browser.

### R4 — An out-of-scope follow-up is answered, not refused (C31)
**Pass:** 1 · **Severity:** high · **Where:** D9, `backend/app/features/context.py`
**What:** Q11 asked after Q1 is searched as Q1 + Q11 and scores 0.645, above `MIN_SCORE`
(0.485). The model then declines in words, but the outcome is `answered`. No threshold
can separate it from genuine follow-ups (evidence: `docs/design/D2-refusal-threshold.md`,
`tickets/T1-F6-follow-up.md`).
**Decision:** ACCEPTED **by the team** (2026-10-08) as a known limitation for the release
gate. C31 and D9 are kept unchanged, and no model-based refusal gate is added. **The release
gate decides whether it blocks.**

### R5 — A corpus change without `--force` would leave stale passages
**Pass:** 1 · **Severity:** low · **Where:** `backend/app/ingest/ingest.py`
**What:** removed or renamed sections kept their old points.
**Decision:** FIXED by F1's fix: on boot the index is rebuilt when its passage count or
dimension no longer matches the corpus and D0. `--force` remains for a manual rebuild.

### R6 — Short, casual questions the policies answer can be refused
**Pass:** 1 (found after the review, in use) · **Severity:** medium · **Where:** D2,
`MIN_SCORE=0.485`
**What:** of 20 natural rewordings of answerable questions, 17 were answered and 3 were
refused:

| Question | Score |
|---|---|
| "what's the hotel limit in Singapore" | 0.435 |
| "hotel cap singapore" | 0.402 |
| "what class can I fly to New York" | 0.448 |

Several more cleared the threshold only narrowly (0.495–0.508). The threshold was fitted to
the 13 fully worded evaluation questions. Casual answerable questions score 0.40–0.45, the
same band as the two that must refuse: Q11 at 0.446 and Q12 at 0.435. So no threshold
fixes it.
**Decision:** **OPEN — for the team / release gate.** Options were put to the project
owner on 2026-10-08:

- A. Add lexical (keyword) matching to retrieval and re-measure D2 on a wider set — the
  agent's recommendation.
- B. Lower `MIN_SCORE`. Rejected by the analysis: it lets Q11 and Q12 through.
- C. Show the nearest sections on a refusal, labelled as not confident enough to answer.

No change has been made, and none has been chosen.

### S1 — Question text leaves the bank, to OpenRouter
**Pass:** 2 · **Severity:** medium · **Where:** `backend/app/generate/client.py` (embed and
generate)
**What:** every question is sent to the embedding and chat providers, and a question can
contain personal data. The brief leaves personal data unresolved.
**Decision:** ACCEPTED — this is the PRD's architecture (§8, OpenRouter), and the
personal-data guardrail (F10) is out of scope by the team's C24. **Flagged for the release
gate.**

### S2 — History is readable by anyone who can reach the API
**Pass:** 2 · **Severity:** medium · **Where:** `backend/app/api/conversations.py`
**What:** `GET /conversations` and `/conversations/{id}` have no authentication, so every
stored question and answer can be read by anyone with the API URL.
**Decision:** ACCEPTED — authentication is out of scope by the team's C24, and history (F8)
is in scope. **Flagged for the release gate:** with F8 shipped and no auth, the live API
exposes all conversations. If that is not acceptable, the remedy is cutting F8, a team
decision.

### M1 — The corpus cache lived in one router and was imported by another
**Pass:** 3 · **Severity:** low · **Where:** `backend/app/api/corpus.py`, `ask.py`
**Decision:** FIXED — now `app.ingest.corpus.documents()`, beside the parser.

### M2 — The API URL fallback was repeated in four pages
**Pass:** 3 · **Severity:** low · **Where:** `frontend/app/**/page.tsx`
**Decision:** FIXED — one `apiUrl()` in `frontend/lib/config.ts`.

### M3 — Dead CSS left behind by F5's first version
**Pass:** 3 · **Severity:** low · **Where:** `frontend/app/globals.css`
**Decision:** FIXED — `.answer-text` and `.citation .passage` removed.

### M4 — The "setting missing → 503" path can no longer trigger
**Pass:** 3 · **Severity:** low · **Where:** `backend/app/api/ask.py` (`get_deps`)
**What:** config now carries the decided values, so `require()` only fires if one is
removed.
**Decision:** ACCEPTED — that is exactly the case it guards: deleting a decision must fail
loudly, not silently. Covered by `test_an_unset_threshold_is_a_clear_503_not_a_guess`.

### M5 — The evaluation tool restates EVALUATION.md's expected sections
**Pass:** 3 · **Severity:** low · **Where:** `backend/app/retrieve/evaluate.py` (`EXPECTED`)
**Decision:** ACCEPTED — `EVALUATION.md` is protected prose, and parsing its "Section"
lines (one has two sections, one has a different shape) would be more fragile than an
explicit table that names its source. The questions themselves are read from the file.

### M6 — History times were in the server's clock, unlabelled
**Pass:** 3 · **Severity:** low · **Where:** `frontend/app/history/page.tsx`
**Decision:** FIXED — formatted in UTC and labelled "UTC".

### P1 — The frontend tree contains LGPL-3.0 binaries, from Next.js
**Pass:** 4 · **Severity:** medium · **Where:** `frontend/package-lock.json`,
`@img/sharp-libvips-*`
**What:** Next.js pulls in `sharp`'s optional native image libraries, licensed
LGPL-3.0-or-later. CI's licence check covers Python only, so nothing flags them.
**Decision:** DEFERRED — this predates T1: the packages are on `table-3` before this
branch, and T1 added none. It is for the project owner and instructors, who own the
scaffold and the CI checks. Not changed here.

### F1 — The deployed service would never have had an index
**Pass:** 5 · **Severity:** high · **Where:** `backend/app/main.py`,
`backend/app/ingest/ingest.py`
**What:** the deployed Qdrant is on Railway's private network, so
`python -m app.ingest` cannot reach it. The live collection would have been missing,
making every question an error, or left at another dimension from an earlier deploy,
making every search fail.
**Decision:** FIXED — on boot, in a background thread, `ensure_index` builds the index
when it is missing, at another dimension, or a different size than the corpus. A matching
index is left alone. It never blocks `/healthz` and never raises. Tests: four in
`test_f1_ingest.py`. Live: `index current: 135 passages at 3072 dimensions`.

### F2 — Qdrant down was an unhandled 500
**Pass:** 5 · **Severity:** medium · **Where:** `backend/app/retrieve/qdrant_store.py`
**Decision:** FIXED — the store raises its own `StoreUnavailable`. `/ask` answers 503
"policy search is unavailable", which the UI shows as an error, not a refusal. Verified
live with Qdrant on a closed port.

### F3 — Postgres down was an unhandled 500
**Pass:** 5 · **Severity:** medium · **Where:** `backend/app/main.py`
**Decision:** FIXED — database errors are a 503 "conversation store is unavailable",
logged by type. Verified live with Postgres on a closed port.

### F4 — A hung model can hold an answer for minutes before degrading
**Pass:** 5 · **Severity:** medium · **Where:** `LLM_TIMEOUT_SECONDS=60` ×
`LLM_MAX_RETRIES=3`
**What:** the user waits on the pending state until every retry times out.
**Decision:** DEFERRED — shortening it trades answers for speed. That belongs with C21,
which the team accepted as a known limitation. Both values are configuration, so a change
needs no code. **For the release gate.**

### F5 — Tables are created only if Postgres is up at startup
**Pass:** 5 · **Severity:** low · **Where:** `backend/app/main.py` (lifespan)
**Decision:** ACCEPTED — `/healthz` reports the database, and a restart creates them. The
same pattern as the scaffold's `ensure_database`.

### F6 — The browser waits indefinitely if the API never answers
**Pass:** 5 · **Severity:** low · **Where:** `frontend/lib/api.ts`
**Decision:** ACCEPTED — the backend bounds its own work (model timeout → degraded, store
or database down → 503). A client-side cut-off would be a new number nobody has decided.

---

## Dependencies

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
| **react-markdown** *(new, approved)* | 10.1.0 | MIT | yes |
| **remark-gfm** *(new, approved)* | 4.0.1 | MIT | yes |
| their 98 transitive packages *(new)* | — | MIT ×97, ISC ×1 | yes |
| next → @img/sharp-libvips-* *(pre-existing)* | — | LGPL-3.0-or-later | **no** — see P1 |

`ci/check_licences.py`: PASS, 59 Python dependencies, all permissive.

## Summary

| | |
|---|---|
| Findings | 21 |
| Fixed | 10 — R1, R2, R5, M1, M2, M3, M6, F1, F2, F3 |
| Accepted | 8 — R3, R4, S1, S2, M4, M5, F5, F6 |
| Deferred | 2 — P1, F4 |
| **Open** | 1 — R6 (for the team / release gate) |

**The one we accepted on purpose, and why:**

**R4 / C31.** An out-of-scope question asked as a follow-up is answered rather than
refused. The team kept C31 as written, and failing, rather than weaken it. It kept D9
rather than change the design without evidence for a better one, and it refused to add a
model-based refusal gate, which would put the refuse-or-answer decision in the model,
where the PRD says it must not be. The release gate decides whether it blocks.

**Also for the release gate:** C21 (median answer 5.23 s against < 5 s), S1 (questions go
to OpenRouter), S2 (history readable without auth) and F4 (slow degrade on a hung model).
