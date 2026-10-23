# T1-F5 — Ask, and show it

**Parent:** [T1](T1.md)
**Feature:** F5 ask + UI
**Covers:** REQ-A1, REQ-A2, REQ-A5, REQ-C1, REQ-C2, REQ-U1, REQ-U1b, REQ-U2, REQ-U3, REQ-U4, REQ-U5, REQ-U6, REQ-U7, REQ-U9, REQ-U10, REQ-U11
**Status:** `done`

## What this is

`POST /ask` ties retrieval, refusal and generation together, stores each turn, and the page renders answered, refused and degraded outcomes with citations visible.
After this, a staff member can ask in a browser and see a cited answer or a refusal.

## Done when

In a browser, a question returns a cited answer, a refusal looks different from an error, and the top bar shows Reset alone.

## How to check it

```bash
cd backend && pytest -q -k "ask or healthz"
cd frontend && npm run typecheck && npm run lint
```

The backend tests pass, the frontend typecheck and lint exit 0, and a manual check in the running app at `localhost:3000` shows the three outcomes rendered differently.

## Decisions this depends on

| | | |
|---|---|---|
| **D7** | how citations are grouped | Decides whether three passages from one document show as one citation or three. |

## What this touches

- `backend/app/api/ask.py` (new router, mounted in `main.py`)
- `backend/app/core/database.py` and a models module for `conversations`, `messages`, `message_citations`
- `frontend/app/page.tsx`, `frontend/components/` (Answer, Refusal, Degraded, Citations, Chat), `frontend/lib/`, `frontend/app/globals.css`
- `backend/tests/` ask and healthz tests

## Not in this feature

- Follow-up context: the turn record exists, but the question is answered alone (F6)
- Corpus routes and the Corpus button (F7)
- History route and the History button (F8)
- Feedback, audit export, guardrails (F9 to F12, beyond the critical path)

## Evidence

> ⚠️ **Required before this ticket can be `done`.** Paste the command you ran and
> the output it produced. CI reads this section, and "works" or "tested" does not
> count — it is a claim, not a record. A ticket marked done on a claim is reported
> as not done.

$ cd backend && python3 -m pytest -q -k "ask or healthz"
16 passed, 87 deselected, 1 warning

$ cd frontend && npm run typecheck && npm run lint
typecheck exit=0
lint exit=0

$ curl -s localhost:8000/healthz
{"status":"ok",...,"model":"anthropic/claude-haiku-5.5 configured"}

$ POST /ask (live, MIN_SCORE=0.50)
"What is the approval threshold for a travel expense claim?" -> answered; cites 4.2 v3.1 current, 4.1 v3.0 superseded
"Do I need approval for a claim of exactly £75?"            -> answered; cites 4.2 v3.1 current, 4.1 v3.0 superseded
"How long must client correspondence be kept?"              -> answered; cites records retention v4.0 current
"What is the best pizza topping in Paris?"                  -> refused; no citations

Browser check at localhost:3000 (reported by the team, "browser passed"):
answered cited view, superseded citation marked, refusal distinct from error, Reset clears.

## Notes

Nothing deploys here. Keep going; everything goes out together at stage 05.

**Blocker resolved.** The table key was missing at first; it was then set in the
API environment. Live outcomes are in Evidence above. The provider-failure path
(503) was tested separately: `/ask` returns 503 when the provider is unreachable,
and the web proxy forwards it.

**Decisions on record (stage 03).**
- D2 refusal threshold: `MIN_SCORE=0.50`. Team said "just use 0.50"; reason
  given: the value accepted in F3 (`T1-F3-refuse.md`).
- 503 on provider failure: accepted the proposal. Reason: an unreachable provider
  is neither an answer nor a refusal, and a refusal would wrongly tell staff the
  policy does not cover the question. Not in PRD §5; the PRD should be updated
  by the team.
- Example questions: accepted the proposal. Reason: each is answerable from the
  corpus, and the first is the superseded-travel-policy case (REQ-U1b). The
  superseded citation is not yet verified live, since the key is missing.
