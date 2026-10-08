# D2 — The refusal threshold

**Decided:** 2026-10-08, table 3, stage 02 decision interview
**Status:** method locked · **value to be measured in stage 03 and brought back for sign-off**

## What we chose

**Method.** Run the 13 evaluation questions and record every score.

- If the answerable (Q1–Q10) and out-of-scope (Q11–Q13) top scores are clearly
  separated, use the midpoint of the gap (option A).
- If they do not separate cleanly, lean towards refusing: set it just below the lowest
  answerable score (option B), rather than force a threshold that lets confident
  unsupported answers through.
- Whether the gap counts as "meaningful" is judged by the team at sign-off, using the
  recorded distribution.

**How it is applied.** Per passage. Every retrieved passage below `MIN_SCORE` is
discarded (REQ-R2). If none survive, we refuse.

**What it is measured on.** Standalone questions **and** the combined text a follow-up
retrieves on (D9), including Q11 asked as a follow-up to Q1.

## Why

The product's stated priority is avoiding confident wrong answers. When the
distributions overlap, B is better than C, which would lean towards answering.

## Consequences

- Determines C4, C5, C7 and refusal behaviour.
- Tuned only after D1, D3, D4, D6 and D9 are in place.
- The scaffold's fallback `MIN_SCORE=0.35` (`backend/app/core/config.py`) is not a
  decision. It must be replaced explicitly by the signed-off value.

## Measured value

*Stage 03. The score distribution (in the format of `backend/corpus/EVALUATION.md`'s
results table), the chosen value and the team's sign-off go here.
`EVALUATION.md` itself is protected and is not edited.*
