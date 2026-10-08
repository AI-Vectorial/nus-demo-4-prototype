# T1-F1 — Ingest the corpus

**Parent:** [T1](T1.md)
**Feature:** F1 Ingest
**Covers:** REQ-I1, REQ-I2, REQ-I3, REQ-I4, REQ-I5, REQ-I6, REQ-I7
**Criteria:** C1, C2, C3, C29
**Status:** `done`

## Done when

`python -m app.ingest` indexes the whole corpus from empty, and running it a second time leaves the passage count and ids unchanged.

## Decisions this depends on

- **D0** — embedding model and dimensions. The Qdrant collection is fixed at the dimension it is first created with, so changing it later means re-indexing.
- **D1** — chunk size, and whether chunks overlap.

## Notes

The two versions of the travel policy share a document id, so a passage id must include the version or v3.1 would overwrite v3.0.

## Evidence

Run 2026-10-08 against the Codespace's Qdrant, with `text-embedding-3-small` (D0) and
`CHUNK_MAX_TOKENS=400`, `CHUNK_OVERLAP_TOKENS=0` (D1). Ids are compared as a digest of
every point id in the collection.

```
== run 1 (empty collection)
created Qdrant collection (dim=1536)
5 documents, 135 passages, 2 embedding requests, 135 passages in the store
ids digest 7ad0db772a98
== run 2
5 documents, 135 passages, 2 embedding requests, 135 passages in the store
ids digest 7ad0db772a98
== --force
deleted Qdrant collection / created Qdrant collection (dim=1536)
5 documents, 135 passages, 2 embedding requests, 135 passages in the store
ids digest 7ad0db772a98
```

Full corpus in about 7.6 s (NFR-4: under 60 s). 135 passages from 169 sections: the 34
heading-only sections are dropped (D1). 2 requests for 135 passages at
`EMBEDDING_BATCH_SIZE=96` (C29).

`tests/features/test_f1_ingest.py`: 12 passed (C1, C2, C3, C29, REQ-I2).
