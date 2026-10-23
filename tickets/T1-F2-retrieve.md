# T1-F2 — Retrieve

**Parent:** [T1](T1.md)
**Feature:** F2 retrieve
**Covers:** REQ-R1, REQ-R5
**Status:** `todo`

## What this is

A function that embeds a question, searches the Qdrant collection, and returns the closest passages with scores and payload.
After this, the question-to-passage path works without a model answer.

## Done when

All ten answerable questions in `backend/corpus/EVALUATION.md` (Q1–Q10) return their expected section in the top three results.

## How to check it

```bash
cd backend && pytest -q -k "retrieval or evaluation"
```

The run reports all Q1–Q10 tests passed. If any fail, the top score and the rank of the expected section are printed for each, and are recorded at stage 04 rather than tuned away.

## Decisions this depends on

| | | |
|---|---|---|
| **D0** | embedding model and dimensions | Must match the collection the corpus was indexed into. |
| **D3** | how many passages to retrieve | Sets `RETRIEVE_TOP_K`. Changes which sections can reach the top three. |

## What this touches

- `backend/app/retrieve/` (a search helper or module that calls `get_vector_store().search`)
- `backend/tests/` evaluation tests for Q1–Q10
- `backend/app/core/config.py`: `RETRIEVE_TOP_K`

## Not in this feature

- The refusal threshold and the decision to refuse (F3)
- Any generation (F4)
- Re-ranking, hybrid search or query expansion, unless measured failing first (out of scope in features.md)

## Evidence

> ⚠️ **Required before this ticket can be `done`.** Paste the command you ran and
> the output it produced. CI reads this section, and "works" or "tested" does not
> count — it is a claim, not a record. A ticket marked done on a claim is reported
> as not done.

```
```

## Notes

The per-question top scores and ranks are the input to D2 at stage 02 and 03.
