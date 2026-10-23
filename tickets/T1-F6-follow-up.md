# T1-F6 — Follow-up questions

**Parent:** [T1](T1.md)
**Feature:** F6 follow-up
**Covers:** REQ-C3, REQ-C4, REQ-C5, REQ-C6, REQ-C7, REQ-A3, REQ-U8
**Status:** `todo` · cuttable

## What this is

A follow-up is answered with recent turns in context, and retrieval still runs on every turn, embedded against the conversation's user turns.
After this, "and what about above £500?" gets its own answer from the right section.

## Done when

Asking "What is the approval threshold for a travel expense claim?" and then "and what about above £500?" returns `answered` for the second, citing the travel policy from a different passage than the first, and Reset starts a fresh conversation.

## How to check it

```bash
cd backend && pytest -q -k "follow or context"
```

The follow-up tests pass, and a manual two-question exchange in the running app shows the second answer citing a different passage from the first.

## Decisions this depends on

| | | |
|---|---|---|
| **D8** | how much conversation a follow-up sees | Sets how many turns (`CONTEXT_MESSAGES`, default 5) the model receives. |
| **D9** | whether a follow-up re-retrieves, and on what text | Decides that retrieval runs every turn on the user turns, not the fragment alone. |

## What this touches

- `backend/app/api/ask.py` (context loading from `messages`)
- `backend/app/retrieve/` (the query text built from user turns)
- `frontend/components/Chat.tsx` (passes `conversation_id`, adds Reset)
- `backend/tests/` follow-up tests

## Not in this feature

- Listing or reopening past conversations (F8)
- Storing the record of turns, which is F5's

## Evidence

> ⚠️ **Required before this ticket can be `done`.** Paste the command you ran and
> the output it produced. CI reads this section, and "works" or "tested" does not
> count — it is a claim, not a record. A ticket marked done on a claim is reported
> as not done.

```
```

## Notes

If cut: every question stands alone, Reset is the only bar action, and the release plan says follow-up is not in this release.
