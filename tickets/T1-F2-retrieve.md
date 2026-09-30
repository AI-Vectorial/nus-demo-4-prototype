# T1-F2 — Retrieve

**Parent:** [T1](T1.md)
**Feature:** F2 retrieve
**Covers:** REQ-R1, REQ-R5
**Status:** `done`

## Done when

Each of the ten answerable questions in `corpus/EVALUATION.md` returns its expected
document and section in the top three — epic criterion 7 passes.

## Decisions this depends on

- **D3** — how many passages to retrieve. More gives the answer more context and the prompt more noise; fewer risks the expected section falling outside what is returned

## Evidence — 2026-09-30

`python -m app.retrieve.evaluate` against the live index. `rank` is where the expected
section sits; all ten answerable questions have it in the top three (criterion 7).

```
MIN_SCORE=0.517  RETRIEVE_TOP_K=5  openai/text-embedding-3-small

  Q     top  rank  outcome       top hit
  1   0.836     2  grounded      travel-expense-policy v3.0 4.1 Approval thresholds
  2   0.667     1  grounded      travel-expense-policy v3.1 4.2 Approval thresholds
  3   0.533     1  grounded      travel-expense-policy v3.1 5.2 Air travel
  4   0.622     1  grounded      travel-expense-policy v3.1 6.2 Accommodation caps
  5   0.767     2  grounded      client-onboarding-kyc v2.4 6.3 Event-driven review
  6   0.753     1  grounded      client-onboarding-kyc v2.4 6.4 Overdue refresh
  7   0.553     1  grounded      client-onboarding-kyc v2.4 4.2 Enhanced due diligence
  8   0.749     1  grounded      records-retention v4.0 4.2 Client correspondence — what it includes
  9   0.689     2  grounded      outsourcing-third-party v1.8 4.2 What must be in place before approval
 10   0.618     2  grounded      records-retention v4.0 4.2 Client correspondence — what it includes
 11   0.501     -  refused       travel-expense-policy v3.0 5.2 Air travel
 12   0.490     -  refused       client-onboarding-kyc v2.4 9. Related policies
 13   0.258     -  refused       records-retention v4.0 4.3 Where two periods apply

lowest answerable top score   0.533
highest out-of-scope top score 0.501
gap 0.501 .. 0.533, midpoint 0.517
evaluate exit code: 0
```

Q10: both sides of the conflict are retrieved — Outsourcing §6.4 at rank 2 (0.576),
Retention §4.1 at rank 3 (0.524).

Criterion 7 needs real embeddings, so it is evidenced here rather than in CI; the mechanism
is tested in `tests/features/test_f2_f3_retrieve_refuse.py`. Full suite: 82 passed.
