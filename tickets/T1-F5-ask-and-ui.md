# T1-F5 — Ask, and show it

**Parent:** [T1](T1.md)
**Feature:** F5 Ask + UI
**Covers:** REQ-A1, REQ-A2, REQ-A5, REQ-C1, REQ-C2, REQ-U1, REQ-U2, REQ-U3, REQ-U4, REQ-U5, REQ-U6, REQ-U7, REQ-U9, REQ-U10, REQ-U11
**Criteria:** C9, C10, C11, C13, C21, C22, C27, C28, and the Reset part of C25
**Status:** `built` — C21 fails (see below); final once D2 is signed off

## Done when

I can ask a question in a browser and see a cited answer, and a refusal looks different from an error.

## Decisions this depends on

- **D7** — how citations are grouped.

## Notes

Nothing deploys at F5. The top bar carries Reset only at this point; Corpus and History are added when their routes land.

C12 (a citation opens its section) depends on F7 and is tracked there.

## Evidence

*All live results below were run with `MIN_SCORE=0.485`, the **proposed** value, set only in the local dev process. It is not signed off and not in configuration.*

Browser check against `localhost:3000`: 29/29 passed. Question, pending state, answer;
citations visible without a click, grouped by document and version, superseded marked
(C10, C11, C13); refusal, degraded and error each look different (C9); Reset (C25);
no horizontal scroll at 390 px, light theme only (C27).

- C22: `test_c22_the_question_is_never_logged` passes. The live log shows the
  troubleshooting line (`ask conversation=… outcome=… latency_ms=…`) and no question text.
- C28: with Postgres and Qdrant pointed at closed ports, `/healthz` returns 200 and reports
  both as `down (unreachable: …)`.
- **C21 FAILS.** Median answer latency: 5.23 s over Q1–Q10, against a target of under 5 s.
  Individual answers range from 2.2 s to 16.4 s, and the time is the model call
  (`LLM_MODEL`, fixed by PRD §8). Median refusal latency: 1.12 s (under 1.5 s, passes).
