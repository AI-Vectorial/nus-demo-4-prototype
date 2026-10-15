# T1-F1 — Ingest the corpus

**Parent:** [T1](T1.md)
**Feature:** F1 ingest
**Covers:** REQ-I1, REQ-I2, REQ-I3, REQ-I4, REQ-I5, REQ-I6, REQ-I7
**Status:** `done`
**Cuttable:** no

## Done when

Running `python -m app.ingest` on an empty collection indexes the corpus, and a second run leaves the passage count unchanged.

**Evidence (2026-10-15, live Qdrant, `policy_passages_table_1`):**
- First run: `ingest: 5 documents, 130 passages, 130 indexed`
- Second run: `ingest: 5 documents, 130 passages, 130 indexed`
- Store count after both runs: 130
- Tests: `tests/features/test_ingest.py`, 11 passed. Full suite 70 passed. `ruff check` clean. `bandit -ll` clean.

## Decisions this depends on

- **D0** — embedding model and dimensions. The collection is fixed at the dimension first indexed.
- **D1** — chunk size and overlap. Sets how passages are split on section boundaries.

## Notes

Acceptance criteria are in [T1](T1.md). Tracking only.
