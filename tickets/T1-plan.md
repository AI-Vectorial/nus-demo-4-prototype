# T1 — Implementation plan

**Stage:** 02 plan
**Ticket:** [tickets/T1.md](T1.md)
**Status:** AWAITING APPROVAL

---

## The decisions

*PRD §10, D0–D9. Options, trade-offs and recommendations were presented in one block on
2026-09-30. The team replied "go with your own recommendation", was shown each
recommendation with its reason, and replied **"confirm all"**. The reasons below are
therefore the agent's recommendations, **confirmed by the team without amendment** —
recorded as such so nobody at the gate mistakes them for independently argued positions.*

| # | Decision | What we chose | Why we chose it |
|---|---|---|---|
| D0 | Embedding model and dimensions | `openai/text-embedding-3-small`, `EMBEDDING_DIMENSIONS=1536` | Already configured locally and on Railway. Upgrade to 3-large only if criterion 7 fails on retrieval quality — one `--force` re-index, then re-tune D2 |
| D1 | Chunk size and overlap | One passage per `###` section (or `##` with no children); `CHUNK_MAX_TOKENS=512` as a safety cap, splitting at sentence ends only if exceeded; `CHUNK_OVERLAP_TOKENS=0`. Embedded text is prefixed with title › parent heading › section | Measured: 164 headings, median 30 words, max 195 (Retention §4.1). Every section fits whole, so no table is ever split and each citation names exactly one section. The prefix gives short sections their context |
| D2 | Refusal threshold, and how we arrived at it | **Method now, number at build.** Run all 13 `EVALUATION.md` questions, record top scores in its table, set `MIN_SCORE` at the midpoint of the gap between lowest answerable and highest out-of-scope. If they overlap, err toward refusing (S5) and name the answerable question that fails. **The number returns to the team for confirmation before F4 starts** | The only option that can answer "how did you arrive at it?". `0.35` in `config.py` is a placeholder, not a choice |
| D3 | Passages retrieved per question | `RETRIEVE_TOP_K=5` | Headroom above the top 3 we test; Q10 needs two documents and v3.0 can take a slot. The threshold still discards weak ones |
| D4 | Superseded policies | **Flag.** Indexed and retrievable, labelled superseded in prompt and citation; the prompt says the current version governs and the older figure may only be mentioned as "previously" | The brief's harm is not knowing which answer is current. Labelled beats hidden; keeps criterion 28 testable |
| D5 | What a refusal says | A fixed template, in a file: the corpus does not cover this; the four policy areas it does cover and their owners; Compliance for anything else | Decided without the model; honest; lets the user route themselves (Q11 → Group Finance) |
| D6 | Two policies conflict | **Surface both.** The prompt instructs: when passages disagree, state both, cite both, name the conflict, do not choose. Outcome stays `answered` | The corpus itself (Outsourcing §6.4) says escalate, not resolve locally; the brief says surface, don't decide |
| D7 | How citations are grouped | One citation per passage, de-duplicated on document + section + version. Visual grouping by document in the UI only if F5 has time | PRD §5 has one `section` per citation and one `message_citations` row each |
| D8 | How much conversation a follow-up sees | **Deferred to F6.** `CONTEXT_MESSAGES=5` stays at the PRD default, unused | It cannot be tested in this increment; an untestable number is not a defensible one |
| D9 | Whether a follow-up re-retrieves | Yes, every turn, on the recent **user** questions concatenated; answer composed for the latest one. Built in F6 | C5: each turn may need new sections. C7: a fragment has no policy vocabulary. User turns only, so old answers don't anchor retrieval |

### Raised while writing the plan — answered 2026-09-30

*Team replied "go with your own recommendation", was shown each recommendation, and replied **"confirm"**.*

| | Question | Options | Recommendation (confirmed) |
|---|---|---|---|
| **P1** | **When the record is written.** ✅ **Chose (a).** The plan template lists this as D8; the PRD's D8 is conversation depth. Raised rather than silently resolved | (a) user + assistant messages in **one transaction after the outcome is known** — never a half turn, but a crash mid-request loses the question · (b) user message **first**, assistant after — the question survives a crash, but a conversation can hold an unanswered turn · (c) write only on `answered` — loses refusals, which S5 needs | **(a).** Refused and degraded are outcomes, not errors, so they are still recorded; only an unhandled exception is lost, and it is logged |
| **P2** | **How `CHUNK_MAX_TOKENS` counts tokens.** ✅ **Chose (a)** — no new dependency. An exact count needs `tiktoken` (MIT) — a new dependency | (a) approximate: characters ÷ 4, no dependency · (b) add `tiktoken`, exact | **(a).** The cap is a safety net no current section approaches; an exact count buys nothing here |

## What we will build

| Order | File | New / Change | What it does |
|---|---|---|---|
| 1 | `backend/app/core/config.py`, `backend/.env.example` | Change | Add `CHUNK_MAX_TOKENS`, `CHUNK_OVERLAP_TOKENS`, `RETRIEVE_TOP_K`; defaults set to the values above |
| 2 | `backend/app/ingest/{loader,chunker,__main__}.py` | New | Read `MANIFEST.yaml` + files, split on headings, stable id = hash(document, version, section, text), batch-embed, upsert; `--force` |
| 3 | `backend/app/retrieve/qdrant_store.py` | Change | Add a `recreate()` for `--force` |
| 4 | `backend/app/retrieve/retrieve.py` | New | Returns `Grounded(hits)` or `Insufficient(reason)` — a type, never an empty list |
| 5 | `backend/app/generate/prompts/answer_v1.md`, `backend/app/generate/refusal.md` | New | The versioned prompt (D4, D6 instructions) and the refusal template (D5) |
| 6 | `backend/app/generate/compose.py` | New | `Grounded` → answer or `Degraded`; kill switch and `ProviderError` both degrade |
| 7 | `backend/app/core/models.py`, `backend/app/api/ask.py`, `backend/app/main.py` | New / Change | Tables per PRD §6; `POST /ask`; record written per P1 |
| 8 | `frontend/app/page.tsx`, `components/*`, `app/history/page.tsx`, `app/corpus/page.tsx` | Change / New | Top bar, empty/pending/answered/refused/degraded/error states, "coming soon" routes |
| — | `backend/tests/features/test_f1..f5_*.py` | New | Criteria 1–33 as tests, written before each piece |

## Why this order

It is the dependency chain: nothing retrieves until ingest works, D2 cannot be measured
until retrieval runs, and the UI renders outcomes the API must already return. Deploy the
moment F5 passes.

## What we will NOT do

- F6 follow-up context, F7 corpus browser, F8 history (routes are "coming soon" only)
- Re-ranking, hybrid search or query rewriting — unless criterion 7 measurably fails, and then only after asking
- Any new dependency (P2 chose none); any edit to `backend/corpus/`
- Streaming, auth, settings UI

## The riskiest part

**Risk:** No threshold separates the 10 answerable from the 3 out-of-scope — most likely
Q12 (crypto vs KYC) or Q11 (partner's flight vs travel) scoring above a weak answerable one.
**If it fails:** stop and bring the score table to the team. Options then: err toward
refusing per D2's rule and record the failed answerable question; improve the embedded
text (D1 prefix); or switch to 3-large (D0) and re-measure. **Never** edit the corpus or
the evaluation set.

---

## Approval

| | |
|---|---|
| **Decision** | |
| **By** | |
| **When** | |
| **If rejected, what would make it acceptable** | |
