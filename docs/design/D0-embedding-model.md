# D0 — Embedding model and dimensions

**Decided:** 2026-10-08, table 3, stage 02 decision interview
**Status:** locked

## What we chose

- `EMBEDDING_MODEL_SLUG=openai/text-embedding-3-small`
- `EMBEDDING_DIMENSIONS=1536`

## Why

- The corpus is small, and we have no evidence yet that we need the larger model. We
  start with the PRD default and set a baseline on the 13 evaluation questions rather
  than pay for extra model capacity on an assumption.
- What matters is retrieval quality, not storage or raw model capability. We evaluate
  that once the other retrieval decisions are made.

## When we would revisit it

If the evaluation shows retrieval problems, we first find out whether the cause is the
embedding model or another retrieval decision (chunking, threshold, top-k, superseded
handling). We change the model only if the evidence points to the model itself.

## Options we did not choose

- `text-embedding-3-large` at 3072: better separation of similar passages, about 6×
  the cost per token, slightly slower.
- `text-embedding-3-large` cut to 1536: most of large's quality at small's size, but
  still large's price.

## Consequences

- The Qdrant collection is created at 1536. Changing it means re-indexing with `--force`
  and re-tuning the D2 threshold.
