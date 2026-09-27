# T1-F1 — Ingest the corpus

**Parent:** [T1](T1.md)
**Feature:** F1 Ingest the corpus
**Covers:** REQ-I1 … REQ-I7
**Status:** `todo`

## Done when

`python -m app.ingest` indexes the corpus, and running it twice changes nothing — same passage count, same ids.

## Decisions this depends on

- **D0** — `text-embedding-3-small`, 1536. Switching to 3072 means `--force` re-indexing; the collection is fixed at the first dimension used
- **D1** — section-first, 400 tokens max, 60 overlap, splitting only on paragraph boundaries. A smaller cap would split sections and make citations vaguer
