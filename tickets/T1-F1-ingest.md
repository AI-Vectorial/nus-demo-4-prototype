# T1-F1 — Ingest the corpus

**Parent:** [T1](T1.md)
**Feature:** F1 ingest
**Covers:** REQ-I1, REQ-I2, REQ-I3, REQ-I4, REQ-I5, REQ-I6, REQ-I7
**Status:** `done`

## Done when

From an empty collection, `python -m app.ingest` indexes all five corpus files, and
running it a second time leaves the passage count and ids unchanged — epic criteria
1 – 6 pass.

## Decisions this depends on

- **D0** — embedding model and dimensions. Fixes the Qdrant collection size at first index; changing it later means `--force` and a full re-embed
- **D1** — chunk size and overlap. Larger chunks make citations vaguer; smaller ones can lose the clause that gives a passage its meaning. Also changes the passage count criteria 3 and 4 compare against

## Evidence — 2026-09-30

`pytest -q tests/features/test_f1_ingest.py` — 12 passed (criteria 1 – 6, fake model and
in-memory store over the real `backend/corpus/`). Full suite: 71 passed.

Live, against the Codespace Qdrant with `openai/text-embedding-3-small`:

```
--- before: Collection `policy_passages` doesn't exist!          (criterion 1: empty)
--- run 1   130 passages indexed in 10.2s   count 130 ids-hash 312db4ec6296
--- run 2   130 passages indexed in 4.1s    count 130 ids-hash 312db4ec6296   (criterion 3)
--- force   dropped Qdrant collection policy_passages
            130 passages indexed in 6.9s    count 130 ids-hash 312db4ec6296   (criterion 4)

passages missing a field: 0                                                   (criterion 2)
travel-expense-policy 3.1 current 31 · outsourcing-third-party 1.8 current 28
client-onboarding-kyc 2.4 current 26 · records-retention 4.0 current 26
travel-expense-policy 3.0 superseded 19                                       (criterion 1, REQ-I7)
```

130 passages from 164 headings: parent headings with no text of their own are skipped
(D1). No section reached the 512-token cap, so no section was split.
`ruff`, `bandit -ll`, scope check and licence check: all pass.
