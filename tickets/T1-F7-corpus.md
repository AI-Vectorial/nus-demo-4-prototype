# T1-F7 — Browse the corpus

**Parent:** [T1](T1.md)
**Feature:** F7 corpus browser
**Covers:** REQ-B1, REQ-B2, REQ-B3, REQ-B4, REQ-B5, REQ-B6, REQ-A4, REQ-U12, REQ-U15
**Status:** `todo` · cuttable

## What this is

`/corpus` lists the five documents, and `/corpus/[id]` shows one document's sections with their Markdown rendered.
After this, clicking a citation opens the section it names.

## Done when

`/corpus` lists all five documents with the superseded travel policy marked, and clicking a citation from an answer opens its section in `/corpus/[id]`.

## How to check it

```bash
cd backend && pytest -q -k corpus
cd frontend && npm run typecheck && npm run lint
```

The corpus tests pass, and in the running app a citation click lands on the correct heading with its tables rendered as tables.

## Decisions this depends on

| | | |
|---|---|---|
| **D4** | whether superseded policies are shown, hidden or flagged | Sets how the superseded document is marked in the list and in citations. |

## What this touches

- `backend/app/api/corpus.py` (new router: `GET /corpus`, `GET /corpus/{id}`, reading `backend/corpus/`)
- `frontend/app/corpus/page.tsx` and `frontend/app/corpus/[id]/page.tsx`
- `frontend/components/Citations.tsx` (links by heading)
- Markdown rendering in the frontend (a library, to be proposed and licence-checked before adding)
- `backend/tests/` corpus route tests

## Not in this feature

- Copying documents into Postgres (REQ-B5 forbids it)
- Editing policy (protected)
- The History route (F8)

## Evidence

> ⚠️ **Required before this ticket can be `done`.** Paste the command you ran and
> the output it produced. CI reads this section, and "works" or "tested" does not
> count — it is a claim, not a record. A ticket marked done on a claim is reported
> as not done.

```
```

## Notes

If cut: no Corpus action in the top bar, and citations stay text.
Link by heading, not anchor (REQ-U15).
