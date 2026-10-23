# T1-F5 — Ask and show the result

**Parent:** [T1](T1.md)
**Feature:** F5 Ask and UI
**Covers:** REQ-A1, REQ-A2, REQ-A5, REQ-C1, REQ-C2, REQ-U1, REQ-U1b, REQ-U2, REQ-U3, REQ-U4, REQ-U5, REQ-U6, REQ-U7, REQ-U9, REQ-U10, REQ-U11
**Status:** `in progress`
**Cuttable:** No

## What this is

Connect ingestion, retrieval, refusal and generation through `POST /ask`, recording each exchange.
Replace the welcome screen with an assistant that clearly renders each response outcome.

## Done when

Pass when a browser question returns a contract-valid cited answer and refusal is visibly different from an error.

## How to check it

```bash
cd backend && pytest -q tests/features/test_ask.py
cd ../frontend && npm run lint && npm run typecheck
```

Pass: API tests validate the three response outcomes; the browser check covers citations, pending state, phone width and working navigation.

## Decisions this depends on

| | | |
|---|---|---|
| **D7** | Citation grouping | The citation panel may group or separate passages according to the selected rule. |

## What this touches

`backend/app/main.py`, new ask/API and persistence modules, `frontend/app/`, `frontend/components/` and `frontend/lib/`.
Keep the §5 API response shape and the existing provider and vector-store boundaries.

## Not in this feature

Follow-up context, corpus browsing and history screens belong to F6–F8.
Do not show a History or Corpus action before its route exists.

## Evidence

> ⚠️ **Required before this ticket can be `done`.** Paste the command you ran and
> the output it produced. CI reads this section, and "works" or "tested" does not
> count — it is a claim, not a record. A ticket marked done on a claim is reported
> as not done.

```
cd backend && pytest -q tests/features/test_ask.py
4 passed, 1 warning in 0.10s

cd frontend && npm run lint && npm run typecheck
ESLint passed; TypeScript check passed.
```

## Notes

API tests use SQLite and controlled retrieval/generation outcomes to validate persistence and response contracts.
Interactive end-to-end browser evidence is pending; the local UI and API are reachable, but the API reports its model credential missing.
