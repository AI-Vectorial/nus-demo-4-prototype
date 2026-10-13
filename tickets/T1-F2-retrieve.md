# T1-F2 — Retrieve

**Parent:** [T1](T1.md)
**Feature:** F2 Retrieve
**Covers:** REQ-R1, REQ-R5
**Status:** `done`

## Done when

The ten answerable questions in `corpus/EVALUATION.md` each return their expected section in the top three.

## Decisions this depends on

- **D3** — six passages. Fewer risks losing one side of Q10's two-document answer; more brings weaker passages into the prompt

## Evidence

Live index, `RETRIEVE_TOP_K=6`, 2026-09-27.

```
$ python -m tests.eval.evaluation
| Q | top score | expected rank(s) | in top 3 | top hit |
|---|---|---|---|---|
| 1 | 0.831 | 2 | yes | travel-expense-policy v3.0 4.1 Approval thresholds |
| 2 | 0.659 | 1 | yes | travel-expense-policy v3.1 4.2 Approval thresholds |
| 3 | 0.526 | 1 | yes | travel-expense-policy v3.1 5.2 Air travel |
| 4 | 0.611 | 1 | yes | travel-expense-policy v3.1 6.2 Accommodation caps |
| 5 | 0.731 | 2 | yes | client-onboarding-kyc v2.4 6.3 Event-driven review |
| 6 | 0.743 | 1 | yes | client-onboarding-kyc v2.4 6.4 Overdue refresh |
| 7 | 0.535 | 1 | yes | client-onboarding-kyc v2.4 4.2 Enhanced due diligence |
| 8 | 0.750 | 2, 1 | yes | records-retention v4.0 4.2 Client correspondence — what it includes |
| 9 | 0.691 | 1 | yes | outsourcing-third-party v1.8 4.1 Approval authority |
| 10 | 0.621 | 2, 3 | yes | records-retention v4.0 4.2 Client correspondence — what it includes |

$ pytest -m live -q tests/eval -k top_three
10 passed
```

## Notes

- Q1's top hit is the **superseded** v3.0 (§4.1, £50) at 0.831, above current v3.1 §4.2. D4 has to handle this in F4
- Q10 finds both sides of the conflict in the top three, which D6 needs
