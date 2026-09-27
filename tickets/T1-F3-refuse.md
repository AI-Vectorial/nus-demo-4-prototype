# T1-F3 — Refuse

**Parent:** [T1](T1.md)
**Feature:** F3 Refuse
**Covers:** REQ-R2, REQ-R3, REQ-R4, REQ-R6
**Status:** `todo`

## Done when

All three out-of-scope questions refuse, and all ten answerable ones do not.

## Decisions this depends on

- **D2** — `MIN_SCORE=0.35` as a starting value; it must refuse Q11–Q13 on the threshold alone, or the number moves. Scores recorded in `docs/design/decisions.md`
- **D5** — the refusal lists the four policy areas and their owning teams, and points to Compliance for anything else. Routing to the nearest document's owner instead would misroute Q12 and Q13
