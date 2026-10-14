# D8 — How much conversation a follow-up sees

**Decided:** 2026-10-08, table 3, stage 02 decision interview
**Status:** locked

## What we chose

Option B — `CONTEXT_MESSAGES=5`, counted as **messages (rows), not turns**. That is
roughly two to three question-and-answer exchanges.

## Why

PRD §6 describes the window as "the last `CONTEXT_MESSAGES` rows". Five messages gives
immediate continuity without letting old topics dominate, and it is the PRD default.

## PRD wording

**Identified PRD wording issue, for the PRD's owner.** REQ-C4 says "turns"; §6 says
"rows". We follow §6. `docs/PRD.md` is protected and we do not modify it. This record is
our interpretation until the owner clarifies the wording.

## Consequences

Affects C14, C20, answer latency and prompt size.

## Careful about

A refusal can stay in context as conversation history, but it is never treated as policy
evidence.
