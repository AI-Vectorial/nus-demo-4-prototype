# D9 — Follow-up retrieval

**Decided:** 2026-10-08, table 3, stage 02 decision interview
**Status:** locked

## What we chose

Option B — retrieval runs on every turn (REQ-C5), on the current question plus the
earlier user questions (REQ-C7) within the D8 window.

**N** is the number of user questions that fall within the last `CONTEXT_MESSAGES` (5)
messages, the current question included. There is no separate D9 setting. Retrieval and
answer context use the same 5-message window; assistant messages are left out of the
retrieval text.

- Assistant answers are never part of the retrieval text.
- No model rewrites the follow-up before retrieval.

## Why

The retrieval query needs earlier user questions to make sense of follow-ups like "what
about that one?". Carrying the whole conversation indefinitely contaminates later topics.
Tying N to D8 keeps the system bounded and easy to understand.

## Options we did not choose

- A — every earlier user question: old topics dominate long conversations.
- C — the model rewrites the question first: calls the model before deciding whether to
  refuse, which breaks C7 and NFR-2.

## Consequences

Affects C14, C20 and, critically, D2: combined retrieval text produces different
similarity scores than a standalone question.

## Careful about

This is the biggest D2 interaction. Asked after Q1, Q11's retrieval text carries strong
travel vocabulary and could clear the threshold even though no policy answers it. Q11 must
be tested as a follow-up to Q1, not only on its own.
