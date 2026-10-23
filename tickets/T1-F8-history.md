# T1-F8 — History

**Parent:** [T1](T1.md)
**Feature:** F8 history
**Covers:** REQ-C8, REQ-C9, REQ-A6, REQ-U13, REQ-U14
**Status:** `todo` · cuttable

## What this is

`/history` lists past conversations, newest first, and opening one shows its turns and accepts a follow-up.
After this, a conversation can be left and resumed with its context intact.

## Done when

A conversation with at least one turn appears in `/history` newest first, and opening it shows its turns and accepts a follow-up that uses the earlier context.

## How to check it

```bash
cd backend && pytest -q -k history
cd frontend && npm run typecheck && npm run lint
```

The history tests pass, and in the running app a past conversation reopens and answers a follow-up.

## Decisions this depends on

| | | |
|---|---|---|
| **D8** | how much conversation a follow-up sees | Applies to a resumed conversation exactly as to a live one. |

## What this touches

- `backend/app/api/conversations.py` (new router: `GET /conversations`, `GET /conversations/{id}`)
- `frontend/app/history/page.tsx` and a conversation view
- `backend/tests/` history tests

## Not in this feature

- Storing conversations: that is F5's (REQ-C1, REQ-C2)
- Authentication or per-user history (out of scope)
- Audit export (F11, beyond the critical path)

## Evidence

> ⚠️ **Required before this ticket can be `done`.** Paste the command you ran and
> the output it produced. CI reads this section, and "works" or "tested" does not
> count — it is a claim, not a record. A ticket marked done on a claim is reported
> as not done.

```
```

## Notes

If cut: no History action in the top bar. Conversations are still persisted, so nothing is lost, only unread.
Title is the first question, truncated. No title column.
