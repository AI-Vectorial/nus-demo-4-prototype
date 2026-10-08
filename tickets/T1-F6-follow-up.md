# T1-F6 — Follow-up questions

**Parent:** [T1](T1.md)
**Feature:** F6 Follow-up *(cuttable)*
**Covers:** REQ-C3, REQ-C4, REQ-C5, REQ-C6, REQ-C7, REQ-A3, REQ-U8
**Criteria:** C14, C15, C31
**Status:** `built` — **C31 fails**; a release-gate decision

## Done when

A follow-up is answered with the earlier context understood and retrieval run again, and Reset starts a clean conversation without deleting saved history.

## Decisions this depends on

- **D8** — how many turns a follow-up sees.
- **D9** — whether a follow-up re-retrieves, and on what text. Decided at stage 02: the user questions within the last 5 messages.

## Notes

Cuttable. If cut, every question stands alone, Reset is the only top-bar action, and the release plan says follow-up is not in this release.

## Evidence

*All live results below were run with `MIN_SCORE=0.485`, the **proposed** value, set only in the local dev process. It is not signed off and not in configuration.*

- C14: "What is the approval limit for travel expenses?" then "What about expenses above
  that limit?" is answered with the £500 and £2,500 tiers. Tests confirm retrieval reran
  on `question 1 + question 2`, and the answer prompt carried the earlier turn.
- C15: Reset (browser) returns to an empty conversation, and the next question starts a
  new conversation id. The earlier one is still in `/history`.
- **C31 FAILS, 3 of 3 runs.** Q11 asked straight after Q1 returns `outcome: answered`, not
  a refusal. The model's text does decline ("the policies provided do not address
  whether a partner's flight can be expensed"), but the criterion is a refusal, and the
  refusal decision is made in code before the model, which here it is not.
  - **Why:** D9 searches on the user questions in the window, so the search text is Q1 +
    Q11. Q1's travel-approval vocabulary pulls the approval-threshold sections up to 0.645,
    well above `MIN_SCORE`.
  - **What was tested:** small and large models, with and without the prefix. C31 scored
    0.595–0.732 in every configuration, always above at least five answerable questions.
    The current question searched alone does not separate either (C14's follow-up
    0.42–0.50, Q11 0.42–0.52).
  - **Why a threshold cannot fix it:** any `MIN_SCORE` above 0.645 refuses Q3, Q4, Q7, Q10
    and C14's follow-up.
  - **Why the design was kept:** the team decided not to weaken C31, not to change D9
    without evidence for a better design, and not to add a model-based refusal gate. The
    release gate decides whether this blocks.
