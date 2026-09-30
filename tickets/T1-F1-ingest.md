# T1-F1 — Ingest the corpus

**Parent:** [T1](T1.md)
**Feature:** F1 ingest
**Covers:** REQ-I1, REQ-I2, REQ-I3, REQ-I4, REQ-I5, REQ-I6, REQ-I7
**Status:** `todo`

## Done when

From an empty collection, `python -m app.ingest` indexes all five corpus files, and
running it a second time leaves the passage count and ids unchanged — epic criteria
1 – 6 pass.

## Decisions this depends on

- **D0** — embedding model and dimensions. Fixes the Qdrant collection size at first index; changing it later means `--force` and a full re-embed
- **D1** — chunk size and overlap. Larger chunks make citations vaguer; smaller ones can lose the clause that gives a passage its meaning. Also changes the passage count criteria 3 and 4 compare against
