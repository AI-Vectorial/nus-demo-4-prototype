# T1-F5 — Ask, and show it

**Parent:** [T1](T1.md)
**Feature:** F5 ask + UI
**Covers:** REQ-A1, REQ-A2, REQ-A5, REQ-C1, REQ-C2, REQ-U1, REQ-U1b, REQ-U2, REQ-U3, REQ-U4, REQ-U5, REQ-U6, REQ-U7, REQ-U9, REQ-U10, REQ-U11
**Status:** `todo`

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

```
```

## Notes

Nothing deploys here. Keep going; everything goes out together at stage 05.
