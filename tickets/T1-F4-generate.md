# T1-F4 — Generate

**Parent:** [T1](T1.md)
**Feature:** F4 Generate
**Covers:** REQ-G1, REQ-G2, REQ-G3, REQ-G4, REQ-G5, REQ-G6
**Criteria:** C4 (grounded-answer half), C8, C30
**Status:** `built` — final once D2 is signed off

## Done when

An answer is composed only from the retrieved passages and carries them, and with `GENERATION_ENABLED=false` or the failing fake model the passages are still returned with no composed answer.

## Decisions this depends on

- **D4** — whether superseded policies are shown, hidden or flagged.
- **D6** — what happens when two policies conflict. Not decided yet; stage 02.

## Notes

The kill switch is part of this feature, not later polish.

## Evidence

*All live results below were run with `MIN_SCORE=0.485`, the **proposed** value, set only in the local dev process. It is not signed off and not in configuration.*

- C4: Q1–Q10 all `answered` on the live model, with the expected sections cited.
- C8: kill switch and failing-model tests pass; in the browser, a backend with
  `GENERATION_ENABLED=false` shows the degraded banner and the passages, with no answer.
- C30: Q10 on `answer-v2`, 4 of 4 live runs: cites Outsourcing v1.8 §6.4 and Records
  Retention v4.0 §4.1, opens with "The policies conflict", sets the two requirements side by
  side, names the escalation to Group Legal and Group Operational Risk, and picks neither.
  (On `answer-v1` it opened with the five-year limit as the answer, which failed C30.)
