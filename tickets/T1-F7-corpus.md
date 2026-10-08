# T1-F7 — Browse the corpus

**Parent:** [T1](T1.md)
**Feature:** F7 Corpus browser *(cuttable)*
**Covers:** REQ-B1, REQ-B2, REQ-B3, REQ-B4, REQ-B5, REQ-B6, REQ-A4, REQ-U12, REQ-U15
**Criteria:** C12, C16, C17, C18, C26, and the Corpus part of C25
**Status:** `todo`

## Done when

Clicking a citation opens the policy section it named, and that section can be read with its tables rendered as tables.

## Decisions this depends on

- None of the PRD §10 decisions.

## Notes

Cuttable. If cut, there is no Corpus action in the top bar and citations stay as text rather than links.

Documents are read from `backend/corpus/`, not copied into the database (REQ-B5). A citation links by heading, not by position (REQ-U15). Adding a Markdown renderer would be a dependency and needs a decision, including its licence, before it goes in.
