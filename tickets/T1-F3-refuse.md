# T1-F3 — Refuse

**Parent:** [T1](T1.md)
**Feature:** F3 Refuse
**Covers:** REQ-R2, REQ-R3, REQ-R4, REQ-R6
**Criteria:** C5, C6, C7
**Status:** `todo`

## Done when

All three out-of-scope evaluation questions are refused and all ten answerable ones are not, and a refusal makes no model call.

## Decisions this depends on

- **D2** — the refusal threshold, and how it was arrived at, tuned against the evaluation set.
- **D5** — what a refusal says.

## Notes

The threshold is read from configuration (REQ-R4). If no threshold separates all 13 questions, stop and say so.
