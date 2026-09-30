# T1-F4 — Generate

**Parent:** [T1](T1.md)
**Feature:** F4 generate
**Covers:** REQ-G1, REQ-G2, REQ-G3, REQ-G4, REQ-G5, REQ-G6
**Status:** `todo`

## Done when

An answer cites only retrieved passages, and with `GENERATION_ENABLED=false` an
answerable question still returns its passages as `degraded` — epic criteria 13 – 19
pass (20 is checked manually at stage 06).

## Decisions this depends on

- **D4** — whether superseded policies are shown, hidden or flagged. Changes what the prompt receives and whether criterion 28 can be exercised
- **D6** — what happens when two policies conflict. Surface both, pick one, or refuse — changes the prompt instruction and possibly the outcome returned
