# T1-F3 — Refuse

**Parent:** [T1](T1.md)
**Feature:** F3 refuse
**Covers:** REQ-R2, REQ-R3, REQ-R4, REQ-R6
**Status:** `todo`

## What this is

Passages below `MIN_SCORE` are discarded, and when none survive, retrieval returns an explicit insufficiency and generation is not called.
After this, an unanswerable question refuses without a model call.

## Done when

Q11, Q12 and Q13 each return insufficiency, and a test asserts `model.was_called` is false for them, with the scores recorded against the live index.

## How to check it

```bash
cd backend && pytest -q -k "refus or insufficien"
```

All refusal tests pass. The live-index run prints each of Q1–Q13 with its top score, and the refused set is Q11–Q13.

## Decisions this depends on

| | | |
|---|---|---|
| **D2** | the refusal threshold, and how it was arrived at | Sets `MIN_SCORE`. Stale if D0 or D1 changes; re-run F2's evaluation and re-tune. |
| **D5** | what a refusal says | Sets the text of the refusal reason, which must point the user onward. |

## What this touches

- `backend/app/retrieve/` (the `Grounded | Insufficient` result type and the threshold filter)
- `backend/app/core/config.py`: `MIN_SCORE` (already present, default `0.35`, to be confirmed at stage 02)
- `backend/tests/` refusal tests, using `model` and `FakeVectorStore`

## Not in this feature

- Composing an answer from passages (F4)
- Rendering a refusal on screen (F5)
- Changing the evaluation set or the corpus (protected)

## Evidence

> ⚠️ **Required before this ticket can be `done`.** Paste the command you ran and
> the output it produced. CI reads this section, and "works" or "tested" does not
> count — it is a claim, not a record. A ticket marked done on a claim is reported
> as not done.

```
```

## Notes

Make refusal a type, not an empty list. Then generation cannot run on a refusal by accident.
