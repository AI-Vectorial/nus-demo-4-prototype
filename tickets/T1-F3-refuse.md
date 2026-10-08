# T1-F3 — Refuse

**Parent:** [T1](T1.md)
**Feature:** F3 Refuse
**Covers:** REQ-R2, REQ-R3, REQ-R4, REQ-R6
**Criteria:** C5, C6, C7
**Status:** `done`

## Done when

All three out-of-scope evaluation questions are refused and all ten answerable ones are not, and a refusal makes no model call.

## Decisions this depends on

- **D2** — the refusal threshold, and how it was arrived at, tuned against the evaluation set.
- **D5** — what a refusal says.

## Notes

The threshold is read from configuration (REQ-R4). If no threshold separates all 13 questions, stop and say so.

## Evidence

*Live results were run with `MIN_SCORE=0.485`, then proposed and since signed off unchanged.*

- C5: Q11, Q12 and Q13 refused (1116 ms, 1054 ms, 1129 ms).
- C6: the refusal states the policies do not support an answer and lists each current
  policy with its owner (browser check: rendered as a refusal, dashed, not as an error).
- C7: `test_c7_a_refusal_never_calls_the_model` passes.
