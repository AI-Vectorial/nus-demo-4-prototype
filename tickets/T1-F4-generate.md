# T1-F4 — Generate

**Parent:** [T1](T1.md)
**Feature:** F4 Generate
**Covers:** REQ-G1 … REQ-G6
**Status:** `todo`

## Done when

An answer cites only retrieved passages, and with `GENERATION_ENABLED=false` `/ask` returns the retrieved passages with outcome `degraded`.

## Decisions this depends on

- **D4** — superseded policy is shown, flagged loudly. Hiding it would make "has this changed?" unanswerable
- **D6** — when two current policies conflict, surface both, name the conflict, do not resolve it. Picking one would make the software decide which policy wins
