# T1-F4 — Generate

**Parent:** [T1](T1.md)
**Feature:** F4 Generate
**Covers:** REQ-G1, REQ-G2, REQ-G3, REQ-G4, REQ-G5, REQ-G6
**Criteria:** C4 (grounded-answer half), C8
**Status:** `todo`

## Done when

An answer is composed only from the retrieved passages and carries them, and with `GENERATION_ENABLED=false` or the failing fake model the passages are still returned with no composed answer.

## Decisions this depends on

- **D4** — whether superseded policies are shown, hidden or flagged.
- **D6** — what happens when two policies conflict. Not decided yet; stage 02.

## Notes

The kill switch is part of this feature, not later polish.
