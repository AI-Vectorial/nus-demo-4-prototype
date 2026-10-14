# D1 — Chunk size and overlap

**Decided:** 2026-10-08, table 3, stage 02 decision interview
**Status:** locked

## What we chose

Option A — one passage per section.

- `CHUNK_MAX_TOKENS=400`
- `CHUNK_OVERLAP_TOKENS=0`

How we read it:

- The document title and section heading go in front of the text that is embedded. The
  citation still points to the actual section.
- Sections that are only a heading, with no body text, are dropped.

## Why

The corpus is already split into small, meaningful sections (169 sections, largest about
270 tokens). Splitting them further would mostly damage tables and lists and create
duplicate retrieval hits. 400 sits comfortably above the largest section, so it is a
safety ceiling, not an active splitter.

## Options we did not choose

- B — 150 tokens with 30 overlap: splits tables and lists, and the overlaps produce
  near-duplicate hits.
- C — 800 tokens, subsections merged: vague citations and a harder threshold to tune.

## Consequences

Clean section-level citations, stable passage ids, simpler D3 and D7, and a direct match
to the section-level evaluation. Changing D1 later means re-indexing and re-tuning D2.
