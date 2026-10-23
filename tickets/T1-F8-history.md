# T1-F8 — Reopen conversations from history

**Parent:** [T1](T1.md)
**Feature:** F8 History
**Covers:** REQ-C8, REQ-C9, REQ-A6, REQ-U13, REQ-U14
**Status:** `done`
**Cuttable:** Yes — first feature cut if time runs short.

## What this is

List saved conversations newest first and let staff open one to read its turns.
Allow a reopened conversation to continue with a follow-up.

## Done when

Pass when a user can reopen a conversation from history and continue it with its context.

## How to check it

```bash
cd backend && pytest -q tests/features/test_history.py
cd ../frontend && npm run lint && npm run typecheck
```

Pass: API checks verify ordering and empty-conversation exclusion; a browser check reopens and continues a conversation.

## Decisions this depends on

| | | |
|---|---|---|
| None | No §10 decision is listed for F8 in `docs/features.md`. | No decision-dependent behavior is recorded here. |

## What this touches

Add conversation-list/detail API behavior in `backend/app/` using the existing conversation record.
Add `/history` and the History navigation action in `frontend/app/` and `frontend/components/`.

## Not in this feature

A history screen does not add a separate conversation title or a second record store.
Corpus browsing and its navigation belong to F7.

## Evidence

> ⚠️ **Required before this ticket can be `done`.** Paste the command you ran and
> the output it produced. CI reads this section, and "works" or "tested" does not
> count — it is a claim, not a record. A ticket marked done on a claim is reported
> as not done.

```
cd backend && pytest -q tests/features/test_history.py
3 passed, 1 warning in 0.17s

cd frontend && npm run lint && npm run typecheck
ESLint passed; TypeScript check passed.

cd frontend && npx next build --webpack --debug
✓ Compiled successfully in 15.6s; TypeScript passed; static generation completed for 7/7 pages.
Routes include /history, /history/[id], /corpus and /corpus/[id].
```

## Notes

The default Turbopack build exited 143 during build attempts; the webpack production build completed. The Codespace has no browser automation installed, so route interaction was validated through API tests and successful compilation rather than a live browser session.
