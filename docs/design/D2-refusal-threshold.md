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

**Status: no value chosen. The scores do not separate, so the build stopped for the team's
review (stage 03, 2026-10-08).**

`python -m app.retrieve.evaluate`, D0 `text-embedding-3-small` 1536, D1 one passage per
section with title + heading prefixed, D3 top-k 5, no threshold applied.
"Score" is the expected section's score for answerable rows (it must survive the
threshold), and the top score of any passage for rows that must refuse.

| | Q | Score | Expected section rank | Must |
|---|---|---|---|---|
| 1 | approval threshold | 0.802 | 2 (v3.0 §4.1 is 1st at 0.829) | answer |
| 2 | exactly £75 | 0.653 | 1 | answer |
| 3 | business class | **0.494** | 1 | answer |
| 4 | Singapore cap | 0.598 | 1 | answer |
| 5 | high-risk refresh | 0.753 | 1 | answer |
| 6 | 90 days overdue | 0.758 | 1 | answer |
| 7 | EDD ownership % | 0.535 | 1 | answer |
| 8 | correspondence retention | 0.754 | 1 (§4.2) | answer |
| 9 | critical outsourcing approval | 0.690 | 1 | answer |
| 10 | the conflict | 0.520 | 2 and 3 (§6.4 0.521, §4.1 0.520) | answer |
| C14 | follow-up "above that limit" | 0.707 | 2 | answer |
| 11 | partner's flight | **0.517** | — (top: v3.1 §5.2 Air travel) | refuse |
| 12 | cryptocurrency | **0.494** | — (top: KYC §9 Related policies) | refuse |
| 13 | parental leave | 0.264 | — | refuse |
| C31 | Q1 then Q11 | **0.732** | — (top: v3.0 §4.1 Approval thresholds) | refuse |

- Lowest expected-section score: **0.494** (Q3). Highest score that must refuse:
  **0.517** standalone (Q11), **0.732** with C31.
- Gap: **−0.023** on the 13 questions alone, **−0.239** with C31. No threshold passes all
  thirteen, and none comes close to passing C31.
- Every expected section is in the top three (C4's retrieval half holds).
- Searched alone, the C14 follow-up scores 0.495 and Q11 scores 0.517, so gating on the
  current question by itself would not separate them either.
