# T1-F1 — Ingest the corpus

**Parent:** [T1](T1.md)
**Feature:** F1 Ingest
**Covers:** REQ-I1, REQ-I2, REQ-I3, REQ-I4, REQ-I5, REQ-I6, REQ-I7
**Status:** `todo`
**Cuttable:** No

## What this is

Index the approved policy documents as section-aligned passages in Qdrant.
Keep each passage traceable to its document, section, version and status.

## Done when

Pass when one ingestion run indexes the corpus and a repeat leaves the count and passage IDs unchanged.

## How to check it

```bash
cd backend && python -m app.ingest
```

Pass: the command exits successfully; the ingestion test checks repeat-run stability, payload, batching and `--force`.

## Decisions this depends on

| | | |
|---|---|---|
| **D0** | Embedding model and dimensions | The vector dimensions and collection setup must match the selected model. |
| **D1** | Chunk size and overlap | Passage boundaries and citation precision change with the chunking choice. |

## What this touches

`backend/app/ingest/`, `backend/app/retrieve/store.py` and the Qdrant adapter; tests live under `backend/tests/features/`.
Read documents from `backend/corpus/`; do not edit or copy them.

## Not in this feature

Searching passages and applying the refusal threshold belong to F2 and F3.
Do not edit policy text to improve indexing.

## Evidence

> ⚠️ **Required before this ticket can be `done`.** Paste the command you ran and
> the output it produced. CI reads this section, and "works" or "tested" does not
> count — it is a claim, not a record. A ticket marked done on a claim is reported
> as not done.

```

```

## Notes

Record evidence from the actual ingestion command and tests at stage 03.
