# T1-F4 — Generate

**Parent:** [T1](T1.md)
**Feature:** F4 generate
**Covers:** REQ-G1, REQ-G2, REQ-G3, REQ-G4, REQ-G5, REQ-G6, REQ-I7
**Status:** `todo`
**Cuttable:** no

## Done when

An answer cites only retrieved passages, and with `GENERATION_ENABLED=false` the product still returns the retrieved passages with a degraded flag and no composed answer.

## Decisions this depends on

- **D4** — how superseded policies are shown, hidden or flagged. The superseded travel policy stays indexed and flagged.
- **D6** — what happens when two policies conflict. Q10 surfaces the conflict; D6 decides nothing beyond that.

## Notes

Acceptance criteria are in [T1](T1.md). Tracking only.
The kill switch is part of this feature, not a later polish.
