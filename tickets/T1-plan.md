# T1 — Implementation plan

**Stage:** 02 plan
**Ticket:** tickets/T1.md
**Status:** AWAITING APPROVAL

---

## The decisions

*All ten, from `docs/PRD.md` §10. Reasons are the ones the team accepted at the
decision interview. Recommendations were the agent's; the team accepted them.*

| # | Decision | What we chose | **Why** |
|---|---|---|---|
| D0 | Embedding model and dimensions | `openai/text-embedding-3-small`, 1536 | Accepted the recommendation. Five short documents; the evaluation set decides quality, not model size. Matches PRD §8. |
| D1 | Chunk size, and whether chunks overlap | One chunk per section, split only if over `CHUNK_MAX_TOKENS`; no overlap. **`CHUNK_MAX_TOKENS` not yet set** | Accepted the recommendation. REQ-I2 and REQ-I3 require section boundaries. The max value is measured from section lengths at stage 03. |
| D2 | The refusal threshold, and how we arrived at it | **Not yet set.** Method: measure top scores for Q1–Q13 on the live index, then set `MIN_SCORE` in the gap between the lowest answerable score and the highest refused score | Accepted the recommendation. The config default `0.35` is not adopted until measured. |
| D3 | How many passages to retrieve | 5 (`RETRIEVE_TOP_K`) | Accepted the recommendation. Enough context to compose; the top-three check still measures ranking. |
| D4 | Superseded policies: shown, hidden or flagged | Indexed and flagged `status: superseded`; shown with status; the answer says when a superseded version was the source | Accepted the recommendation. Smallest change meeting REQ-I7 and REQ-U4. |
| D5 | What a refusal says | One fixed message naming the owning function of the nearest document (from `MANIFEST.yaml`) | Accepted the recommendation. Meets the "where to go instead" requirement. |
| D6 | What happens when two policies conflict | Surface both passages and name the conflict; do not pick one | Accepted the recommendation. Outsourcing §6.4 says not to resolve it locally. |
| D7 | How citations are grouped | One citation per document and section, keeping the highest score | Accepted the recommendation. Names the section exactly, with no repeats. |
| D8 | How much conversation a follow-up sees | 5 turns (`CONTEXT_MESSAGES`) | Accepted the recommendation. Bounds cost; matches the config default. |
| D9 | Whether a follow-up re-retrieves, and on what text | Retrieval runs on every turn, embedding the conversation's user turns, most recent weighted in | Accepted the recommendation. Meets REQ-C5 (always retrieve) and REQ-C7 (embed with prior questions). |

> ⚠️ **Two values are open, and the team has not set them:** D1's `CHUNK_MAX_TOKENS`
> and D2's `MIN_SCORE`. Both are measured at stage 03. A value written into config
> before that measurement is a finding for the gate, not a setting.
>
> ⚠️ **D0 and D2 are coupled.** Change D0 or D1 and the threshold is stale; the product
> refuses everything while every test stays green. If D0 or D1 moves, re-run the
> evaluation and re-tune D2.

## What we will build

| Order | File | New / Change | What it does |
|---|---|---|---|
| 1 | `backend/app/ingest/` (`__init__.py`, `__main__.py`, loader, chunker) | Fill (empty today) | Reads the five corpus files, splits on section headings, hashes stable passage ids, embeds in batches, upserts (F1) |
| 2 | `backend/app/retrieve/` (search module) | New | Embeds the query text built from user turns, searches with `RETRIEVE_TOP_K`, returns `Grounded \| Insufficient` (F2, F3) |
| 3 | `backend/app/generate/prompts/answer_v1.md` | New | Versioned prompt; composes only from passages (F4) |
| 4 | `backend/app/generate/compose.py` | New | Calls `generate()` with passages only; returns `answered` or `degraded` (F4) |
| 5 | `backend/app/models/` (conversation, message, citation ORM) | New | `conversations`, `messages`, `message_citations` per PRD §6 (F5) |
| 6 | `backend/app/api/ask.py` | New; mounted in `main.py` | `POST /ask` ties F1–F4 together and writes turns (F5) |
| 7 | `frontend/app/page.tsx`, `frontend/components/*`, `frontend/lib/*`, `globals.css` | Change | Empty state, answer, refusal, degraded and error views; top bar with Reset only (F5) |
| 8 | `backend/app/api/corpus.py`; `frontend/app/corpus/*` | New (F7, cuttable) | Corpus list and document views; citation links by heading |
| 9 | `backend/app/api/conversations.py`; `frontend/app/history/*` | New (F8, cuttable) | List and reopen conversations |

Context lookup for F6 (last `CONTEXT_MESSAGES` user turns) lives in `ask.py` and the retrieve module.

## Why this order

Each feature needs the one before it: nothing can be retrieved before the corpus is indexed (F1), nothing can refuse before retrieval scores exist (F2 before F3), and nothing can be shown before an answer exists (F4 before F5). The cuttable features come last, so cutting them removes the least.

## What we will NOT do

- Re-rank, hybrid search or query expansion. Only if measured failing.
- Streaming, authentication, a settings page, or any editing of `backend/corpus/` or other protected paths.
- Any model call outside `app.generate`; the provider-boundary test forbids it.
- F9 to F12 until F1–F8 is merged and deployed.
- Pushing to `origin`. Publication is blocked (403); the branch stays local until access is decided.

## The riskiest part

**Risk:** the refusal threshold does not separate answerable from unanswerable questions on the live index, so either answers are refused or invented ones pass.
**If it fails:** record the score distribution and the best achievable split, state which way we erred and why, and bring it to the team as a decision. Do not tune the corpus or the evaluation set.

**Risk two:** `OPENROUTER_API_KEY_TABLE_4` is missing, so embedding and generation cannot run.
**If it fails:** stage 03 stops and the blocker goes to an instructor. Nothing is faked with another key.

---

## Approval

*A role, not a name. Nobody signs anything today.*

| | |
|---|---|
| **Decision** | AWAITING APPROVAL |
| **By** | the release manager |
| **When** | *(pending)* |
| **If rejected, what would make it acceptable** | |
