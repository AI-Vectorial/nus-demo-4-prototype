# T1-F8 — History

**Parent:** [T1](T1.md)
**Feature:** F8 History *(cuttable)*
**Covers:** REQ-C8, REQ-C9, REQ-A6, REQ-U13, REQ-U14
**Criteria:** C19, C20, and the History part of C25
**Status:** `todo`

## Done when

I can leave a conversation, reopen it from `/history`, and ask a follow-up that still has its context.

## Decisions this depends on

- None of the PRD §10 decisions.

## Notes

Cuttable, and the first to go. If cut, there is no History action in the top bar. Conversations are still stored, because that belongs to F5, so nothing is lost.

A conversation with no turns is never listed (REQ-U14). The title is the first question, truncated, with no separate title column.
