# T1-F1 — Ingest the corpus

**Parent:** [T1](T1.md)
**Feature:** F1 ingest
**Covers:** REQ-I1, REQ-I2, REQ-I3, REQ-I4, REQ-I5, REQ-I6, REQ-I7
**Status:** `done`

## What this is

A command that reads the five corpus documents, splits them on section boundaries, embeds them and writes them to Qdrant.
After this, the corpus is searchable and running the command twice changes nothing.

## Done when

Running `python -m app.ingest` twice leaves the passage count and passage ids unchanged, and the count is non-zero after the first run.

## How to check it

```bash
cd backend && python -m app.ingest && python -m app.ingest && pytest -q -k ingest
```

Both runs exit 0, the log shows the same passage count on each, and `pytest -q -k ingest` reports all passed.

## Decisions this depends on

| | | |
|---|---|---|
| **D0** | embedding model and dimensions | Fixes the Qdrant collection dimension. Changing it later means `--force` and re-embedding. |
| **D1** | chunk size and overlap | Sets how many passages exist and where section boundaries fall. |

## What this touches

- `backend/app/ingest/` (currently empty): loader, chunker, id hashing, `__main__` entry point
- `backend/app/retrieve/qdrant_store.py`: upsert and collection creation, used as is
- `backend/tests/` ingest tests
- `backend/app/core/config.py`: reads `CHUNK_MAX_TOKENS` and `CHUNK_OVERLAP_TOKENS` if they are not already present

## Not in this feature

- Retrieval and scores (F2)
- Any change to `backend/corpus/` (protected)
- Automatic re-indexing on change (out of scope in PRD §11)

## Evidence

> ⚠️ **Required before this ticket can be `done`.** Paste the command you ran and
> the output it produced. CI reads this section, and "works" or "tested" does not
> count — it is a claim, not a record. A ticket marked done on a claim is reported
> as not done.

```
$ cd backend && pytest -q
66 passed, 1 warning in 1.84s
$ ruff check .
All checks passed!
$ python -m app.ingest      # run 1
indexed 164 passages; collection now holds 164
$ python -m app.ingest      # run 2
indexed 164 passages; collection now holds 164
```

Passage count is 164 on both runs (REQ-I4). Ids are UUIDs derived from document, version, section and text.
Not yet proven live: `--force` (REQ-I5). `reset()` is written but not run against Qdrant.

## Notes

- Stable passage id, a hash of document, version, section and text, makes REQ-I4 hold. The version is in the hash because v3.0 and v3.1 share a document id.
- D1 taken as the simplest reading: one passage per section, no splitting. `CHUNK_MAX_TOKENS` is not introduced. Section lengths are measured before any split is considered.
- `QdrantVectorStore.reset()` is added for `--force`. It is not on the `VectorStore` protocol, so the fixture store is unchanged.
- Finding: this Codespace has `QDRANT_COLLECTION=policy_passages` and `DATABASE_NAME=policy`. PRD §8 says these are set per table (`policy_passages_table_4`, `table_4`). Config is outside this stage's scope, so it is raised, not changed.
