# T1 — Implementation plan

**Stage:** 02 plan
**Ticket:** tickets/T1.md
**Status:** APPROVED

---

## The decisions

*From PRD section 10. Every row carries the team's reason, in the team's words. Full record: `docs/design/decisions.md`.*

| # | Decision | What we chose | **Why we chose it** |
|---|---|---|---|
| D0 | Embedding model and dimensions | `text-embedding-3-small`, 1536 | Verified working. 3072 doubles cost and storage for a five-document corpus that is not hard to search. Re-indexing later is one command |
| D1 | Chunk size and overlap | Section-first, 400 tokens max, 60 overlap; only a section over 400 splits, on paragraph boundaries | Policy is already written in numbered sections, and a citation to "4.2 Approval thresholds" is something a human can verify |
| D2 | Refusal threshold, and how we arrived at it | `MIN_SCORE=0.35` as a starting value, set below the lowest true answerable score. **Condition:** must refuse Q11–Q13 on the threshold alone, or it moves | A threshold set to catch everything refuses valid rephrasings. Scores for all 13 recorded in `docs/design/decisions.md` during build |
| D3 | Passages retrieved per question | `RETRIEVE_TOP_K=6` | Enough for an answer spanning two sections; few enough that the weakest is still relevant |
| D4 | Superseded policies | Show, flagged loudly | "Has this changed?" stays answerable. An answer citing a withdrawn policy is the failure we exist to prevent, so it has to be impossible to miss |
| D5 | What a refusal says | What is not covered, the four policy areas and their owning teams, and Compliance for anything else. No model call | "I don't know" leaves the user where they started. Every document names an owner in its front matter |
| D6 | Two policies conflict | Surface both, name the conflict, do not resolve it | A governance problem Aldermere already has. Resolving it in code makes our software decide which policy wins |
| D7 | Citation grouping | One per section, deduplicated, highest score wins | Grouping by document would lose the section, which is the part a human can check |
| D8 | Conversation a follow-up sees | `CONTEXT_MESSAGES=5` — *F6, not built in T1* | Enough for "and what about above 500?"; more drags answers toward earlier topics |
| D9 | Follow-up re-retrieval | Every turn, on the earlier user turns + the question — *F6, not built in T1* | Reusing passages answers from the wrong section; the fragment alone matches nothing |

## What we will build

*Each feature: tests first (`backend/tests/features/test_<feature>.py`), red, then code, then green.*

| Order | File | New / Change | What it does |
|---|---|---|---|
| 1 | `backend/app/core/config.py` | Change | Adds `CHUNK_MAX_TOKENS`, `CHUNK_OVERLAP_TOKENS`, `RETRIEVE_TOP_K`; removes the literal `0.35` default so every §10 value comes only from the environment |
| 2 | `backend/app/ingest/chunk.py` | New | Reads front matter; splits on section headings; splits a section over the cap on paragraph boundaries, overlap in whole sentences; id = hash of document, version, section, text |
| 3 | `backend/app/ingest/__main__.py` | New | `python -m app.ingest [--force]`: chunk, batch-embed, upsert with the §7 payload incl. `status`, `version` |
| 4 | `backend/app/retrieve/retrieve.py` | New | `retrieve(question) -> Grounded \| Insufficient`: embed, search top-k, discard below `MIN_SCORE` |
| 5 | `backend/tests/eval/test_evaluation.py` | New | Runs the 13 EVALUATION questions against the live index; prints scores for the D2 table |
| 6 | `backend/app/features/refusal.py` | New | Builds the D5 refusal from front-matter owners. Takes only `Insufficient` |
| 7 | `backend/app/generate/prompts/answer_v1.md` | New | Versioned prompt: passages only; flag superseded (D4); name conflicts, don't resolve (D6) |
| 8 | `backend/app/generate/answer.py` | New | `compose(Grounded) -> Answered \| Degraded`; kill switch on `GENERATION_ENABLED=false` or `ProviderError`; records model, prompt version, latency |
| 9 | `backend/app/core/models.py` | New | `conversations`, `messages`, `message_citations` exactly per PRD §6 |
| 10 | `backend/app/api/ask.py`, `main.py` | New, Change | `POST /ask` per §5; dedupes citations (D7); writes the turn; mounted in `main.py` |
| 11 | `frontend/lib/types.ts`, `lib/api.ts` | Change | Align to §5 — scaffold has `exchange_id`; §5 has `conversation_id`, `message_id` |
| 12 | `frontend/components/TopBar.tsx` | New | Product name + **Reset only** |
| 13 | `frontend/components/Chat.tsx`, `Answer`, `Citations`, `Refusal`, `Degraded`, new `Error.tsx` | Change | Empty state, pending, three outcomes + error each rendered distinctly; superseded badge on citations |

## Why this order

It is the dependency chain F1 → F5: nothing retrieves until something is indexed, and D2 cannot be set honestly until retrieval produces the thirteen scores (step 5), so refusal comes after it. Deploy as soon as F5 works.

## What we will NOT do

- F6+ — no follow-up context, corpus browser, history, feedback, guardrail, export or confidence
- History or Corpus buttons (REQ-U9 deviation, recorded in T1)
- Detect conflicts in code — D6 is handled by the prompt and checked by Q10
- Re-ranking, hybrid search, query expansion, streaming, auth, a settings page
- Edit `backend/corpus/` or any protected path — if retrieval is weak, we fix retrieval
- Add a dependency without asking — token counts are approximated from words, not `tiktoken`

## The riskiest part

**Risk:** 0.35 does not separate the sets — Q12 (cryptocurrency) scores above it against the KYC policy, or an answerable question scores below it. Second risk: D4 and D6 depend on the prompt, so Q1 could answer £50 or Q10 could pick a side.
**If it fails:** raise `MIN_SCORE` to just above the highest out-of-scope score and re-run all thirteen. If no single value passes all thirteen, stop and bring the score table to the team — we do not lean on the model to decline and we do not touch the corpus. For D4/D6, revise the prompt as `answer_v2.md` and re-check Q1 and Q10.

## Open question for the gate

The plan template lists **D8 as "When the record is written"**; PRD §10 lists D8 as how much conversation a follow-up sees. We answered the PRD's. **"When the record is written" was not asked and is not decided.** Default in step 10 would be: write the turn after the outcome is known, for all three outcomes — the team should confirm or change that.

---

## Approval

| | |
|---|---|
| **Decision** | APPROVED |
| **By** | msv, table 3 |
| **When** | 2026-09-27 |
| **If rejected, what would make it acceptable** | — |
