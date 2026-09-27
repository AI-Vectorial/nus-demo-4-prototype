# T1-F4 — Generate

**Parent:** [T1](T1.md)
**Feature:** F4 Generate
**Covers:** REQ-G1 … REQ-G6
**Status:** `done`

## Done when

An answer cites only retrieved passages, and with `GENERATION_ENABLED=false` `/ask` returns the retrieved passages with outcome `degraded`.

## Decisions this depends on

- **D4** — superseded policy is shown, flagged loudly. Hiding it would make "has this changed?" unanswerable
- **D6** — when two current policies conflict, surface both, name the conflict, do not resolve it. Picking one would make the software decide which policy wins

## Evidence

Live index and `openai/gpt-oss-120b`, prompt `answer_v1`, 2026-09-27.

```
=== Q1: What is the approval threshold for a travel expense claim?
passages: [(travel 3.1 4.2), (travel 3.0 4.1), (travel 3.1 4.1), (travel 3.1 2.4), (travel 3.1 4.3), (travel 3.1 3.)]
Answered  model=openai/gpt-oss-120b prompt=answer_v1 latency_ms=8512
- Below £75 – the claim is automatically approved on submission; no manager action is required.
- £75 or more – line-manager approval is required before reimbursement (the £75 threshold is inclusive).
- £500 or more – both line-manager and Department Head approvals are required.
- £2,500 or more – line-manager, Department Head, and Group Finance approvals are required.
(Travel and Expense Policy v3.1, Section 4.2 Approval thresholds)

=== Q2: Does a claim of exactly £75 need approval?
Answered  latency_ms=3259
Yes. A claim of exactly £75 requires line-manager approval before reimbursement (the £75
threshold is inclusive)【Travel and Expense Policy v3.1, 4.2 Approval thresholds】.

=== Q10: A provider holds our client correspondence. How long can they keep it after we terminate?
passages: [(retention 4.0 4.2), (outsourcing 1.8 6.4), (retention 4.0 4.1), (kyc 2.4 7.2)]
Answered  latency_ms=9785
- Records Retention: client correspondence retained 7 years from the end of the client relationship (v4.0, 4.1)
- Outsourcing: provider must destroy all copies within five years of termination (v1.8, 6.4)
- ...escalate the conflict to Group Legal and Group Operational Risk jointly (v1.8, 6.4)
Resulting conflict: ... the policy directs escalation ... rather than a local resolution.

=== Q1 with generation off: Degraded generation disabled 6 passages
```

- **D4:** Q1 retrieves superseded v3.0 (£50) at rank 2 and answers from current v3.1 (£75)
- **D6:** Q10 sets out both, names the conflict, does not choose
- **REQ-G6:** generation off returns the passages, no answer, no model call. Provider failure is covered by `test_an_unreachable_provider_returns_the_passages_with_no_answer`

```
$ pytest -q tests/features/test_generate.py
11 passed
```

## Notes

- **Q3:** EVALUATION.md expects a plain "No"; v3.1 §5.2 also permits business class without approval when the employee works on the day of arrival and lands after 06:00. The answer states both, and both are in the passage. Not a hallucination — a corpus nuance the evaluation set does not mention
- **Latency:** 3.1s, 3.3s, 8.5s, 9.8s on these four. NFR-1 (under 5s at p50) is out of this ticket's criteria by the team's decision, but on this sample it is **not met**. Carried to review
- Citation formatting varies (brackets vs 【】); the UI shows citations from the API, not from the answer text
