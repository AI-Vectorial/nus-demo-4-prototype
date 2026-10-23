# T1-F7 — Browse cited policy documents

**Parent:** [T1](T1.md)
**Feature:** F7 Corpus browser
**Covers:** REQ-B1, REQ-B2, REQ-B3, REQ-B4, REQ-B5, REQ-B6, REQ-A4, REQ-U12, REQ-U15
**Status:** `todo`
**Cuttable:** Yes — cut after F8 if time runs short.

## What this is

List the approved policy documents and let staff read a document's sections.
Make citations navigable to the section they name.

## Done when

Pass when clicking a citation opens its named section and the section text is readable.

## How to check it

```bash
cd backend && pytest -q tests/features/test_corpus.py
cd ../frontend && npm run lint && npm run typecheck
```

Pass: API checks cover document metadata; browser checks cover Markdown, section navigation, citation links and return paths.

## Decisions this depends on

| | | |
|---|---|---|
| None | No §10 decision is listed for F7 in `docs/features.md`. | No decision-dependent behavior is recorded here. |

## What this touches

Add corpus API routes and readers under `backend/app/`; read source files from `backend/corpus/`.
Add `/corpus` and `/corpus/[id]` pages and citation links in `frontend/app/` and `frontend/components/`.

## Not in this feature

Editing policies or copying their contents into the database is not part of browsing.
Conversation history and follow-up handling belong to F6 and F8.

## Evidence

> ⚠️ **Required before this ticket can be `done`.** Paste the command you ran and
> the output it produced. CI reads this section, and "works" or "tested" does not
> count — it is a claim, not a record. A ticket marked done on a claim is reported
> as not done.

```

```

## Notes

If cut for time, remove the Corpus action and citation links with the routes.
