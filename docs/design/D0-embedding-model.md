# D0 — Embedding model and dimensions

**Decided:** 2026-10-08, table 3, stage 02 decision interview
**Status:** locked · **revised 2026-10-08, stage 03, on measured evidence**

## Revision — 2026-10-08, stage 03

**Now:** `EMBEDDING_MODEL_SLUG=openai/text-embedding-3-large`, `EMBEDDING_DIMENSIONS=3072`,
with the D1 title + section-heading prefix kept exactly as decided.

**Team's reason:** the condition this record set for revisiting the model was met.

- `text-embedding-3-small` does not separate the 13 evaluation questions (gap −0.023).
- `text-embedding-3-large` with the prefix gives a +0.078 gap, and every expected section
  stays in the top three.
- It keeps the D1 chunking decision exactly. The large-model experiment without the
  prefix had a slightly larger gap (+0.091), but the team rejected it because it would
  change D1 too.

Evidence: `docs/design/D2-refusal-threshold.md`, experiments 3a and 3b. The collection was
re-indexed with `--force` at 3072: 135 passages, ids unchanged.

---

## The original decision

### What we chose

- `EMBEDDING_MODEL_SLUG=openai/text-embedding-3-small`
- `EMBEDDING_DIMENSIONS=1536`

### Why

- The corpus is small, and we have no evidence yet that we need the larger model. We
  start with the PRD default and set a baseline on the 13 evaluation questions rather
  than pay for extra model capacity on an assumption.
- What matters is retrieval quality, not storage or raw model capability. We evaluate
  that once the other retrieval decisions are made.

### When we would revisit it

If the evaluation shows retrieval problems, we first find out whether the cause is the
embedding model or another retrieval decision (chunking, threshold, top-k, superseded
handling). We change the model only if the evidence points to the model itself.

### Options we did not choose

- `text-embedding-3-large` at 3072: better separation of similar passages, about 6×
  the cost per token, slightly slower.
- `text-embedding-3-large` cut to 1536: most of large's quality at small's size, but
  still large's price.

### Consequences

- The Qdrant collection is created at 1536. Changing it means re-indexing with `--force`
  and re-tuning the D2 threshold.
