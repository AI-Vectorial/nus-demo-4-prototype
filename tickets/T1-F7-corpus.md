# T1-F7 — Browse the corpus

**Parent:** [T1](T1.md)
**Feature:** F7 Corpus browser *(cuttable)*
**Covers:** REQ-B1, REQ-B2, REQ-B3, REQ-B4, REQ-B5, REQ-B6, REQ-A4, REQ-U12, REQ-U15
**Criteria:** C12, C16, C17, C18, C26, and the Corpus part of C25
**Status:** `done`

## Done when

Clicking a citation opens the policy section it named, and that section can be read with its tables rendered as tables.

## Decisions this depends on

- None of the PRD §10 decisions.

## Notes

Cuttable. If cut, there is no Corpus action in the top bar and citations stay as text rather than links.

Documents are read from `backend/corpus/`, not copied into the database (REQ-B5). A citation links by heading, not by position (REQ-U15). Adding a Markdown renderer would be a dependency and needs a decision, including its licence, before it goes in.

## Evidence

`tests/features/test_f7_corpus.py`: 5 passed (C16, C17 at the API; version selection; 404).

Browser check (Playwright, headless Chromium, run from the scratchpad, not a project
dependency) against `localhost:3000` → `localhost:8000`, 2026-10-08: **29/29 checks
passed.** The only console entry was the request the check aborted on purpose to test the
error state.

- C16: `/corpus` lists 5 documents; the superseded v3.0 carries the badge.
- C17: `/corpus/[id]` renders every section with its text; the section list links to each.
- C12, C18: clicking citation "4.1 Approval thresholds" (v3.0) opens
  `/corpus/travel-expense-policy?version=3.0#4-1-approval-thresholds`, and that section is
  the one marked (`:target`), with the same heading.
- C26: policy tables render as `<table>` (6 on travel v3.0, 3 on records retention), with
  no raw `|---` in the page.
- C25 (Corpus part): the top bar offers Corpus, and it opens.
