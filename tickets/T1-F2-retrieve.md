# T1-F2 — Retrieve policy passages

**Parent:** [T1](T1.md)
**Feature:** F2 Retrieve
**Covers:** REQ-R1, REQ-R5
**Status:** `todo`
**Cuttable:** No

## What this is

Embed a question and find its closest indexed policy passages.
Return ranked passages with their source metadata and scores.

## Done when

Pass when every answerable evaluation question returns its expected section in the top three.

## How to check it

```bash
cd backend && pytest -q tests/features/test_retrieval.py
```

Pass: all ten answerable evaluation cases have the expected section among the top three.

## Decisions this depends on

| | | |
|---|---|---|
| **D3** | Number of passages to retrieve | The number of returned candidates changes how much policy context downstream features receive. |

## What this touches

`backend/app/retrieve/` and the embedding interface in `backend/app/generate/`; retrieval tests go under `backend/tests/features/`.
Use the existing `VectorStore` contract and Qdrant adapter rather than adding a second storage path.

## Not in this feature

Classifying insufficient evidence and refusing belong to F3.
Answer composition and the browser ask flow belong to F4 and F5.

## Evidence

> ⚠️ **Required before this ticket can be `done`.** Paste the command you ran and
> the output it produced. CI reads this section, and "works" or "tested" does not
> count — it is a claim, not a record. A ticket marked done on a claim is reported
> as not done.

```

```

## Notes

Keep the live evaluation output with the test evidence at stage 03.
