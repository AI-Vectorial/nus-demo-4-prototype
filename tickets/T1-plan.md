# T1 — Implementation plan

**Stage:** 02 plan
**Ticket:** [tickets/T1.md](T1.md) · F1–F8 in one increment, F6–F8 cuttable
**Status:** APPROVED

---

## The decisions

*PRD §10. The team's reasons are below; the full records are in `docs/design/D0`–`D9`.*

| # | Decision | What we chose | **Why we chose it** (team) |
|---|---|---|---|
| D0 | Embedding model and dimensions | `text-embedding-3-small`, 1536 | Small corpus, no evidence we need more. Set a baseline first. Change the model only if evidence points at the model and not the other retrieval decisions |
| D1 | Chunk size and overlap | One passage per section · `CHUNK_MAX_TOKENS=400` · overlap 0 | Sections are already small and meaningful (largest ≈270 tokens). 400 is a safety ceiling, not a splitter. Splitting harms tables and creates duplicate hits |
| D2 | Refusal threshold, and how | Midpoint of the gap if Q1–10 and Q11–13 separate clearly, otherwise just below the lowest answerable score. Applied **per passage**. **Value measured in stage 03 and brought back for sign-off** | The priority is no confident wrong answers, so lean towards refusing when the evidence overlaps. Measured on standalone and follow-up text. 0.35 is not a decision |
| D3 | Passages retrieved | `RETRIEVE_TOP_K=5` | 3 leaves no room for Q1's two versions or Q10's two documents. 8 adds noise without evidence. It's a ceiling, not a citation count |
| D4 | Superseded policies | Retrieve and flag. The answer prefers current and mentions the old version only when relevant | Hiding it makes historical questions impossible. Downranking adds a parameter that tangles D2 |
| D5 | What a refusal says | Fixed text plus the corpus's policy areas and owners, from metadata. No model call | "I don't know" is too vague. Naming the nearest owner guesses from evidence we just called insufficient. Never invent a contact |
| D6 | Two policies conflict | Surface both, name the conflict, give the escalation route. Never pick one | The software has no authority to decide which policy wins. Refusing hides real evidence and fails C4. Checked by C30 |
| D7 | Citation grouping | API: one per section. UI: grouped under document. A citation = every passage passed to the model | Deterministic and auditable. Grouping is presentation only, and the §5 contract is unchanged |
| D8 | Conversation a follow-up sees | `CONTEXT_MESSAGES=5`, counted as **messages**, not turns | PRD §6 says rows. Enough continuity without old topics taking over. Refusals stay as history, never as evidence |
| D9 | Follow-up retrieval | Every turn, on the user questions within those 5 messages. No answers, no model rewrite, no extra setting | REQ-C5 and REQ-C7 both apply. A bounded window that's easy to explain. Checked by C31 |

## What we will build

| Order | File | New / Change | What it does |
|---|---|---|---|
| 1 | `backend/.env.example`, `app/core/config.py` | Change | Adds `CHUNK_*` and `RETRIEVE_TOP_K`. Sets D0–D9 values in one file. Removes the 0.35 `MIN_SCORE` fallback so a missing value fails loudly |
| 2 | `app/ingest/corpus.py`, `app/ingest/__main__.py` | New | Reads front matter and splits on headings. Drops heading-only sections. Embeds title + heading + text. Stable id from document, **version** and section. Batches by `EMBEDDING_BATCH_SIZE`. `--force` recreates (F1) |
| 2 | `app/retrieve/qdrant_store.py` | Change | Collection recreation for `--force`. Per-passage threshold already in `search` |
| 3 | `app/retrieve/retrieve.py` | New | Returns **Grounded(passages) or Insufficient**, a type and not an empty list (REQ-R3). Builds the D9 query text (F2) |
| 4 | `app/features/refuse.py`, `backend/prompts/refusal-v1.md` | New | D5 text plus the owner directory from corpus metadata. Never calls the model (F3) |
| 5 | `app/generate/answer.py`, `backend/prompts/answer-v1.md` | New | Versioned prompt with D4 and D6 instructions. Records `prompt_version`, `model`, `latency_ms`. Kill switch and `ProviderError` → degraded (F4) |
| 6 | `app/core/models.py`, `app/api/ask.py`, `app/main.py` | New / Change | §6 tables. `POST /ask` per §5. Stores every turn and citation (F5) |
| 6 | `frontend/lib/types.ts`, `components/*`, `app/page.tsx` | Change | Aligns types with §5 (`conversation_id`, `message_id` replace `exchange_id`). Citations grouped by document, superseded marked. Refusal, degraded and pending states. Top bar with Reset (F5) |
| 7 | `app/api/ask.py` | Change | Follow-up context and Reset (F6) |
| 8 | `app/api/corpus.py`, `frontend/app/corpus/**` | New | List and detail, section links by **heading**, tables rendered (F7) |
| 9 | `app/api/conversations.py`, `frontend/app/history/**` | New | List newest first, open and continue (F8) |
| — | `backend/tests/features/test_*.py` | New | One test per criterion, written before its code. Fake and failing models for C7, C8, C30 (citations), C31 |

## Why this order

`features.md`'s critical path: nothing answers until F1 indexes and F2 retrieves. D2 is measured as soon as F2 plus D9's query builder exist, before generation is built on top of it. F6–F8 come last so that cutting them leaves a whole product.

## What we will NOT do

- Edit the corpus, `EVALUATION.md`, the PRD or anything under `pipeline/`, `ci/` or `.github/`
- Change the §5 contract, §6 data model or §7 payload. Fields may be added, nothing renamed
- Pick a `MIN_SCORE` without your sign-off, or adjust anything to force a pass
- Rewrite follow-ups with a model, or ask the model which passages it used
- C24's out-of-scope list: settings, auth, streaming, corpus editing, outside knowledge, F9–F12
- Add any dependency beyond the two below

## The riskiest part

**Risk:** no `MIN_SCORE` separates all 13 questions **and** C31. Q12 (crypto, next to KYC) and Q11 asked after Q1 (travel vocabulary carried over) are the most likely to score above a weak answerable question.
**If it fails:** stop and bring the score distribution to the team, per D2 and T1's open question. We do not edit the corpus, the questions or the criteria. Fixes go only to retrieval, such as the D1 embedding prefix, and each one is reported. If the gap stays closed, the plan leans towards refusing and the team decides.

**Second risk:** C30's wording depends on the model. Citations are tested automatically. The conflict and escalation wording are read on the live answer at stage 06.

## Dependencies (team decisions)

- **`react-markdown` + `remark-gfm`** (both MIT), for C26. Team's reason: GFM tables are exactly what's needed, and we don't maintain bespoke Markdown parsing.
- **No `tiktoken`.** The 400 ceiling is estimated from word count. Team's reason: the largest section is ≈270 tokens and 400 is a safety ceiling, not a precision requirement. Revisit only if a future corpus gets near the ceiling.

---

## Approval

| | |
|---|---|
| **Decision** | APPROVED |
| **By** | Project owner / requester |
| **When** | 2026-10-08 05:45 UTC |
| **Conditions** | None |
| **If rejected, what would make it acceptable** | n/a |
