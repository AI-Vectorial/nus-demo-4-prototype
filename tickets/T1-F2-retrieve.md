# T1-F2 — Retrieve

**Parent:** [T1](T1.md)
**Feature:** F2 retrieve
**Covers:** REQ-R1, REQ-R5
**Status:** `done`

## What this is

A function that embeds a question, searches the Qdrant collection, and returns the closest passages with scores and payload.
After this, the question-to-passage path works without a model answer.

## Done when

All ten answerable questions in `backend/corpus/EVALUATION.md` (Q1–Q10) return their expected section in the top three results.

## How to check it

```bash
cd backend && pytest -q && python -m app.retrieve.evaluate
```

`pytest` covers the mechanism with fakes. `evaluate` runs Q1–Q10 on the live index with real embeddings, and prints `answerable: N/10 pass`. Any failure is recorded at stage 04, not tuned away.

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
- Q11–Q13 refusal itself (F3). F2 only records their scores
- Q4 finding: the top hit is superseded v3.0 §6.1, and current v3.1 §6.2 is second. Handled by D4 in F4, not here
- Any generation (F4)
- Re-ranking, hybrid search or query expansion, unless measured failing first (out of scope in features.md)

## Evidence

> ⚠️ **Required before this ticket can be `done`.** Paste the command you ran and
> the output it produced. CI reads this section, and "works" or "tested" does not
> count — it is a claim, not a record. A ticket marked done on a claim is reported
> as not done.

```
$ cd backend && pytest -q && ruff check .
72 passed, 1 warning in 2.39s
All checks passed!
$ python -m app.retrieve.evaluate
Q1  PASS  top=0.7062  ...   Q2  PASS  top=0.7135  ...   Q3  PASS  top=0.5616
Q4  PASS  top=0.6614  ...   Q5  PASS  top=0.5420  ...   Q6  PASS  top=0.5934
Q7  PASS  top=0.5906  ...   Q8  PASS  top=0.7306  ...   Q9  PASS  top=0.6045
Q10 PASS  top=0.5938  ...
answerable: 10/10 pass
Q11 top=0.4352   Q12 top=0.4684   Q13 top=0.2799
```

Full per-question output, with the top three and their scores, is in the terminal log of this commit's run.
Refusal scores for D2 (F3 sets the value): lowest answerable top score 0.5420 (Q5); highest unanswerable 0.4684 (Q12). The gap is 0.4684 to 0.5420. Not set here.
