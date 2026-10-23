# T1-F6 — Continue with follow-up questions

**Parent:** [T1](T1.md)
**Feature:** F6 Follow-up
**Covers:** REQ-C3, REQ-C4, REQ-C5, REQ-C6, REQ-C7, REQ-A3, REQ-U8
**Status:** `done`
**Cuttable:** Yes — cut after F8 and F7 if time runs short.

## What this is

Let a user ask a follow-up in the same conversation with recent turns available as context.
Run retrieval again on the conversation's user questions, and let Reset start clean.

## Done when

Pass when a follow-up uses recent context, retrieval runs again, and Reset starts a new conversation.

## How to check it

```bash
cd backend && pytest -q tests/features/test_follow_up.py
```

Pass: the test observes prior context, a new retrieval call and a fresh conversation after Reset.

## Decisions this depends on

| | | |
|---|---|---|
| **D8** | How much conversation a follow-up sees | The configured context window determines which recent turns are available. |
| **D9** | Whether a follow-up re-retrieves and on what text | The retrieval query changes with the chosen conversation text; retrieval must still run. |

## What this touches

Conversation persistence and ask orchestration in `backend/app/`, plus the assistant state and API client in `frontend/`.
Add coverage under `backend/tests/features/` for context, retrieval and Reset.

## Not in this feature

Browsing saved conversations belongs to F8.
Do not reuse old passages instead of retrieving again for a follow-up.

## Evidence

> ⚠️ **Required before this ticket can be `done`.** Paste the command you ran and
> the output it produced. CI reads this section, and "works" or "tested" does not
> count — it is a claim, not a record. A ticket marked done on a claim is reported
> as not done.

```
cd backend && pytest -q tests/features/test_follow_up.py
2 passed, 1 warning in 0.19s

cd frontend && npm run lint && npm run typecheck
ESLint passed; TypeScript check passed.
```

## Notes

Retrieval embeds the current question with recent user questions; generation receives the same complete turns as reference context, not policy evidence.
Reset clears the client conversation and ignores any response from a request started before Reset.
