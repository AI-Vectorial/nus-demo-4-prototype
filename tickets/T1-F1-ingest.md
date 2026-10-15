# T1-F1 — Ingest the corpus

**Parent:** [T1](T1.md)
**Feature:** F1 ingest
**Covers:** REQ-I1, REQ-I2, REQ-I3, REQ-I4, REQ-I5, REQ-I6, REQ-I7
**Status:** `todo`
**Cuttable:** no

## Done when

Running `python -m app.ingest` on an empty collection indexes the corpus, and a second run leaves the passage count unchanged.

## Decisions this depends on

- **D0** — embedding model and dimensions. The collection is fixed at the dimension first indexed.
- **D1** — chunk size and overlap. Sets how passages are split on section boundaries.

## Notes

Acceptance criteria are in [T1](T1.md). Tracking only.
