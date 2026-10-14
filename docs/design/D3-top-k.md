# D3 — How many passages to retrieve

**Decided:** 2026-10-08, table 3, stage 02 decision interview
**Status:** locked

## What we chose

Option B — `RETRIEVE_TOP_K=5`.

## Why

Three is too tight for the corpus's deliberately difficult cases. Q1 can pull in both
travel versions, Q10 needs two different current documents, and other questions may need
neighbouring sections. Eight adds prompt length and distraction without enough evidence
that the extra recall is worth it.

## Options we did not choose

- A — 3: no slack for the superseded duplicate or the conflict.
- C — 8: longer prompts, more distraction, long citation lists.

## Consequences

Affects recall, latency, prompt size, citations, D4 and D6. Five is the retrieval
ceiling, not a citation count. D2 can remove some of them.
