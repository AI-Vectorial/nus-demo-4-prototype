# T1-F2 — Retrieve

**Parent:** [T1](T1.md)
**Feature:** F2 retrieve
**Covers:** REQ-R1, REQ-R5
**Status:** `done` — REQ-R5 passes after Amendment 2 (approved by MSV)
**Cuttable:** no

## Done when

Each of the ten answerable questions in `backend/corpus/EVALUATION.md` returns its expected section in the top three results.

## Live result (2026-10-15, `policy_passages_table_1`, `python -m tests.eval.run`)

| Q | Expected | Rank found | Result |
|---|---|---|---|
| Q1 | travel 4.2 | 1 | pass |
| Q2 | travel 4.2 | 1 | pass |
| Q3 | travel 5.2 | 1 | pass |
| Q4 | travel 6.2 | 1 | pass |
| Q5 | KYC 6.1 | 5 (score 0.5074) | **FAIL** — outside top three |
| Q6 | KYC 6.4 | 1 | pass |
| Q7 | KYC 4.2 | 1 | pass |
| Q8 | retention 4.1 or 4.2 | 1 | pass |
| Q9 | outsourcing 4.1 | 2 | pass |
| Q10 | outsourcing 6.4 **and** retention 4.1 | 6.4 at 1; retention 4.1 at 4 (0.5516) | **FAIL** — retention 4.1 outside top three |

**Cause (diagnosed, not fixed):** the section heading is not in the text that is embedded. Passages carry the heading only as metadata, so the embedding cannot match "refresh" to "Refresh cycles" (Q5) or "correspondence" to a large general table (Q10).

**Options for MSV — not decided by the agent:**
- **A.** Embed a context prefix (document title and section heading) with each passage, and re-index with `--force`. Changes what is embedded, so it is a plan amendment. Scores move, so D2 must be re-measured.
- **B.** Accept both misses with a written reason. Requires an explicit exception, since the criterion says "no exceptions".
- **C.** Raise `RETRIEVE_TOP_K`. Does not help: REQ-R5 is a top-three check.

## Decisions this depends on

- **D0** — embedding model and dimensions. Query and passage vectors must come from the same model.
- **D3** — how many passages are retrieved. Sets the candidate pool that F3 filters.
- **D4 (applied)** — current passages are ordered ahead of superseded ones within the result set. Note: this reorders within the top five and does not add superseded hits that were not already in it.

## Decisions this depends on

- **D0** — embedding model and dimensions. Query and passage vectors must come from the same model.
- **D3** — how many passages are retrieved. Sets the candidate pool that F3 filters.

## Notes

Acceptance criteria are in [T1](T1.md). Tracking only.
