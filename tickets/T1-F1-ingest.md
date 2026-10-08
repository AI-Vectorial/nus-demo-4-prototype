# T1-F1 — Ingest the corpus

**Parent:** [T1](T1.md)
**Feature:** F1 Ingest
**Covers:** REQ-I1, REQ-I2, REQ-I3, REQ-I4, REQ-I5, REQ-I6, REQ-I7
**Criteria:** C1, C2, C3, C29
**Status:** `todo`

## Done when

`python -m app.ingest` indexes the whole corpus from empty, and running it a second time leaves the passage count and ids unchanged.

## Decisions this depends on

- **D0** — embedding model and dimensions. The Qdrant collection is fixed at the dimension it is first created with, so changing it later means re-indexing.
- **D1** — chunk size, and whether chunks overlap.

## Notes

The two versions of the travel policy share a document id, so a passage id must include the version or v3.1 would overwrite v3.0.
