# T1-F3 — Refuse unsupported questions

**Parent:** [T1](T1.md)
**Feature:** F3 Refuse
**Covers:** REQ-R2, REQ-R3, REQ-R4, REQ-R6
**Status:** `in progress`
**Cuttable:** No

## What this is

Discard passages below the configured support threshold and represent insufficiency explicitly.
A refusal stops before generation so the model cannot fill gaps in policy evidence.

## Done when

Pass when answerable evaluation questions remain supported and out-of-scope questions return insufficiency without a generation call.

## How to check it

```bash
cd backend && pytest -q tests/features/test_refusal.py
```

Pass: evaluation cases assert the expected outcomes and a refusal leaves the model-call count unchanged.

## Decisions this depends on

| | | |
|---|---|---|
| **D2** | Refusal threshold and how it is determined | The threshold determines which retrieved passages are sufficient to proceed. |
| **D5** | Refusal wording | The selected wording changes the refusal response, not the no-generation behavior. |

## What this touches

`backend/app/retrieve/` and the F3 result type/flow; add focused cases under `backend/tests/features/`.
Read the threshold from configuration and preserve the explicit refusal outcome.

## Not in this feature

Composing an answer from supported passages belongs to F4.
Do not let the model choose whether evidence is sufficient.

## Evidence

> ⚠️ **Required before this ticket can be `done`.** Paste the command you ran and
> the output it produced. CI reads this section, and "works" or "tested" does not
> count — it is a claim, not a record. A ticket marked done on a claim is reported
> as not done.

```
cd backend && pytest -q tests/features/test_refusal.py tests/features/test_retrieval.py tests/features/test_ingest.py
8 passed, 1 warning in 0.35s
```

## Notes

The refusal type and no-generation branch are covered offline.
The final threshold and all 13 evaluation scores remain pending live-index calibration (D2).
