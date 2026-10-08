# T1-F8 — History

**Parent:** [T1](T1.md)
**Feature:** F8 History *(cuttable)*
**Covers:** REQ-C8, REQ-C9, REQ-A6, REQ-U13, REQ-U14
**Criteria:** C19, C20, and the History part of C25
**Status:** `done`

## Done when

I can leave a conversation, reopen it from `/history`, and ask a follow-up that still has its context.

## Decisions this depends on

- None of the PRD §10 decisions.

## Notes

Cuttable, and the first to go. If cut, there is no History action in the top bar. Conversations are still stored, because that belongs to F5, so nothing is lost.

A conversation with no turns is never listed (REQ-U14). The title is the first question, truncated, with no separate title column.

## Evidence

`tests/features/test_f8_history.py`: 8 passed (C19 newest first, title, pagination,
U14 empty never listed; C20 turns and citations, continue with context; 404).

Browser check (Playwright, headless Chromium, run from the scratchpad, not a project
dependency) against `localhost:3000` → `localhost:8000`, 2026-10-08: **29/29 checks
passed.** The only console entry was the request the check aborted on purpose to test the
error state.

- C19: `/history` lists the conversations, newest first.
- C20: opening one shows its turns, and a follow-up asked there is answered in the same
  conversation.
- C25 (History part): the top bar offers History, and it opens.
