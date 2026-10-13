# T1-F3 — Refuse

**Parent:** [T1](T1.md)
**Feature:** F3 Refuse
**Covers:** REQ-R2, REQ-R3, REQ-R4, REQ-R6
**Status:** `done`

## Done when

All three out-of-scope questions refuse, and all ten answerable ones do not.

## Decisions this depends on

- **D2** — `MIN_SCORE=0.51`, revised from 0.35 after it grounded Q11 and Q12 live; confirmed by the team. Scores recorded in `docs/design/decisions.md`
- **D5** — the refusal lists the four policy areas and their owning teams, and points to Compliance for anything else. Routing to the nearest document's owner instead would misroute Q12 and Q13

## Evidence

Live index, `MIN_SCORE=0.51`, `RETRIEVE_TOP_K=6`, 2026-09-27. Retrieval only — no model call on any line.

```
Q1  answer expected answer ok  683ms
Q2  answer expected answer ok  696ms
Q3  answer expected answer ok  758ms
Q4  answer expected answer ok  704ms
Q5  answer expected answer ok  514ms
Q6  answer expected answer ok  797ms
Q7  answer expected answer ok  439ms
Q8  answer expected answer ok  436ms
Q9  answer expected answer ok  451ms
Q10 answer expected answer ok  449ms
Q11 REFUSE expected REFUSE ok  432ms
Q12 REFUSE expected REFUSE ok  440ms
Q13 REFUSE expected REFUSE ok  435ms

$ pytest -m live -q tests/eval
23 passed
$ pytest -q tests/features/test_refuse.py
7 passed
```

The refusal (D5), identical for every out-of-scope question:

```
Aldermere's policy set does not cover this question, so I have not answered it.

I can only answer from these policies. If your question belongs to one of them, its owning team can help:

- Client Onboarding and KYC Refresh Policy — Financial Crime Compliance
- Outsourcing and Third-Party Risk Policy — Group Operational Risk
- Records Retention and Data Handling Policy — Group Legal and Company Secretariat
- Travel and Expense Policy — Group Finance

For anything else, contact Compliance.
```
