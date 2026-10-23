# T1 — Implementation plan

**Stage:** 02 plan
**Ticket:** tickets/T1.md
**Status:** AWAITING APPROVAL

---

## The decisions

| # | Decision | What we chose | **Why** |
|---|---|---|---|
| D0 | Embedding model/dimensions | `openai/text-embedding-3-small`, 1536 | Accepted: configured already; lower cost, with retrieval measured before reconsidering. |
| D1 | Chunk size/overlap | 400 tokens, 50 overlap; section/sentence boundaries | Accepted: focused citations with boundary context. |
| D2 | Refusal threshold/method | `MIN_SCORE`: midpoint between highest out-of-scope and lowest answerable score if separated; otherwise report overlap | Accepted: measured, not guessed; numeric score comes from the live index. |
| D3 | Passage count | Top 5 | Accepted: useful coverage; verify expected section in top three. |
| D4 | Superseded policies | Include and visibly flag | Accepted: preserve history without implying it is current. |
| D5 | Refusal wording | “I can’t find enough support for an answer in the indexed policy. Please contact Compliance.” | Accepted: states evidence limit and gives a next step. |
| D6 | Policy conflict | Show both and the conflict; do not choose; refer to Compliance | Accepted: surface governance, do not decide it in code. |
| D7 | Citation grouping | Group by document, section, version; retain highest score | Accepted: deduplicate without losing source precision. |
| D8 | Conversation context | 5 recent complete turns; `CONTEXT_MESSAGES=5` | Accepted: PRD default balances continuity and bounded context. |
| D9 | Follow-up retrieval | Every turn; current question + recent user questions, not assistant answers | Accepted: refresh search and resolve fragmentary follow-ups. |

> ⚠️ **D0 and D2 are coupled**, and **D9 is REQ-C5.** Change D0 or D1 and the threshold
> in D2 is stale — the product refuses everything while every test stays green. Skip
> retrieval on a follow-up and you answer confidently from the *previous* question's
> passages, which looks right and is not.

## What we will build

| Order | File(s) | Change | Purpose |
|---|---|---|---|
| 1 | `backend/app/ingest/{__main__,parser,chunker}.py`; `tests/features/test_ingest.py` | Add | CLI, section parsing/chunking, batch embedding, stable upserts, `--force`; test idempotence/payload. |
| 2 | `backend/app/retrieve/{query,store,qdrant_store}.py`; retrieval/refusal tests | Change / add | Ranked search, explicit insufficiency, configured threshold and live evaluation. |
| 3 | `backend/app/generate/prompts/v1.md`, `backend/app/features/answer.py`; generation tests | Add | Versioned grounded prompt, metadata, kill switch and degraded response. |
| 4 | `backend/app/api/ask.py`, `backend/app/features/ask.py`, `backend/app/core/{config,models}.py`, `backend/app/main.py`; ask tests | Add / change | Config, persistence, contract-valid API, health and orchestration. |
| 5 | `frontend/app/{page,history/page,corpus/page,corpus/[id]/page}.tsx`, components and `frontend/lib/{api,types}.ts` | Change / add | Ask UI, outcomes, follow-ups, corpus/history routes and citation navigation. |
| 6 | `backend/tests/features/`, frontend checks, feature tickets | Add / change | Verify acceptance; record real output and update status/evidence. |

## Why this order

Build in dependency order: ingestion → retrieval/refusal → generation → ask/API → UI and extensions.
F6–F8 follow the ask flow and are cut in the required order if time is short.

## What we will NOT do

- No protected-file/corpus edits, settings page, authentication, streaming, web search or unapproved dependency.
- No resolution of policy conflicts by software; no history/corpus/follow-up action appears unless its feature ships.

## The riskiest part

**Risk:** The selected embeddings and chunks may not separate answerable from out-of-scope evaluation scores.
**If it fails:** Record scores, then ask the team which approved decision to revisit; do not guess a threshold or edit the corpus.

---

## Approval

*A role, not a name. Nobody signs anything today — do not ask who approved it.*

| | |
|---|---|
| **Decision** | APPROVED |
| **By** | the release manager |
| **When** | 2026-10-23 08:52 UTC |
| **If rejected, what would make it acceptable** | |
