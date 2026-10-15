# T1 — Implementation plan

**Stage:** 02 plan
**Ticket:** [T1](T1.md)
**Table:** 1
**Status:** AWAITING APPROVAL
**Decision numbering:** PRD §10 (the plan template's D8 row is not in PRD §10 and is not used here)

---

## The decisions

*Choices as given by the team. Where no reason was given in the team's words, the row says so.
The agent has not supplied reasons.*

| # | Decision | What we chose | Why we chose it |
|---|---|---|---|
| D0 | Embedding model and dimensions | `openai/text-embedding-3-small`, 1536 dimensions. Validate against Q1–Q10 on the live index | *Reason not given. Required before approval.* |
| D1 | Chunk size and overlap | About 500 tokens, no overlap. Split on section boundaries first. Verify Q10's two clauses land in the top three | *Reason not given. Required before approval.* |
| D2 | Refusal threshold, and how we arrived at it | Tune for maximum separation between Q1–Q10 and Q11–Q13. Record all 13 scores | Maximum separation, as stated. Scores are measured at stage 03 |
| D3 | Passages retrieved per question | 5 | *Reason not given. Required before approval.* |
| D4 | Superseded policies: show, hide or flag | Retain superseded policies. Flag every citation with its status. Prefer current versions when ranking | *Reason not given. Required before approval.* Note: the ranking rule is a behaviour change, not only a display choice |
| D5 | What a refusal says | State the information gap, and direct the user to Group Finance | *Reason not given.* Satisfies the agreed criterion on refusals |
| D6 | What happens when two policies conflict | Surface both conflicting passages and name the conflict. Do not decide which policy prevails. Keep the governance decision open beyond this increment | Matches the agreed criterion for Q10 |
| D7 | How citations are grouped | By section | *Reason not given.* |
| D8 | How much conversation a follow-up sees | 5 turns (PRD default), unless testing shows drift | Keeps the PRD default. Re-check if drift appears |
| D9 | Whether a follow-up re-retrieves, and on what text | Re-retrieve on every turn. Embed the conversation's user turns, latest turn last | *Reason not given.* Matches REQ-C5 and REQ-C7 |

## What we will build

Built in the order below. Configuration lives in `backend/app/core/config.py`, not in code.

| Order | File | New / Change | What it does |
|---|---|---|---|
| 1 | `backend/app/core/config.py` | Change | Add `CHUNK_MAX_TOKENS` (D1), `CHUNK_OVERLAP_TOKENS` (D1, value 0), `RETRIEVE_TOP_K` (D3, value 5). Keep `EMBEDDING_MODEL_SLUG` (D0) and `MIN_SCORE` (D2). Set `CONTEXT_MESSAGES` default 5 (D8) |
| 2 | `backend/app/ingest/` | New | Load `backend/corpus/`, split on section boundaries, cap at about 500 tokens, embed in batches, upsert with stable ids. Includes `python -m app.ingest` and `--force` (F1) |
| 3 | `backend/app/retrieve/` | New | Embed the query, search Qdrant, return `Grounded` or `Insufficient`, never an empty list (F2, F3) |
| 4 | `backend/app/generate/` | New | Versioned prompt file, answer composed only from passages, degraded path when `GENERATION_ENABLED=false` or provider unreachable (F4) |
| 5 | `backend/app/api/ask.py` and `backend/app/main.py` | New / Change | `POST /ask`, conversation and message storage in Postgres (F5) |
| 6 | `frontend/components/`, `frontend/app/page.tsx` | Change | Ask view, citations grouped by section, refusal, error and degraded states, Reset (F5) |
| 7 | F6 files in `backend/app/features/` and the conversation path | New, cuttable | Follow-up retrieval using D8 and D9 |
| 8 | F7 corpus routes and pages, F8 history routes and pages | New, cuttable | Only if they survive review |
| 9 | `backend/tests/` | New | Acceptance tests for each feature, before the code they check where practical |

## Why this order

Each step depends on the one before it. Nothing can be retrieved before it is ingested, and no answer can be composed before retrieval decides whether it is grounded. Configuration goes first so every later step reads the same settings. The cuttable features come last, so cutting them leaves the core intact.

## What we will NOT do

- No edits to `backend/corpus/` or any protected path.
- No settings page, authentication, streaming, re-ranking, hybrid search or query expansion.
- No re-indexing on document change.
- No decision on D6 beyond surfacing the conflict.
- No tuned threshold value written into code. It is measured and recorded at stage 03.
- No corpus content added to the database. Corpus is read from `backend/corpus/`.

## The riskiest part

**Risk:** D2 is tuned against D0 and D1. Any later change to the embedding model or chunk size makes the threshold stale. The product would then refuse everything, while tests still pass.

**If it fails:** Re-run the full 13-question evaluation, record the new scores, and re-tune D2 before anything else. Do not edit the corpus or the questions to fit.

## Open before approval

- Reasons for D0, D1, D3, D4, D5, D7 and D9 are required in the team's own words.
- D2 threshold value is not set until stage 03 measures it.
- The plan template's D8 row and "PRD section 9" reference are out of step with PRD §10. The template is protected and is not changed.

---

## Approval

| | |
|---|---|
| **Decision** | AWAITING APPROVAL |
| **By** | *(MSV, on approval)* |
| **When** | *(timestamp on approval)* |
| **If rejected, what would make it acceptable** | |
