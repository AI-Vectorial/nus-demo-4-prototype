# D4 — Superseded policies

**Decided:** 2026-10-08, table 3, stage 02 decision interview
**Status:** locked

## What we chose

Option B — retrieve and flag.

Superseded policies stay searchable and retrievable. Their citations clearly say they are
superseded. The answer prefers the current policy and mentions the old version only when
it is relevant to the question or explains a change.

## Why

Hiding v3.0 makes legitimate historical questions impossible. Downranking adds another
retrieval parameter and makes D2 harder to reason about. Flagging keeps the information
and makes its status explicit.

## Options we did not choose

- A — hide (filter to current): historical questions become unanswerable.
- C — downrank: a second tuning constant that interacts with D2.

## Consequences

Affects Q1/Q2, citation rendering, degraded mode and D3's slots.

## Careful about

The model must not treat v3.0's £50 as current when v3.1 says £75. In degraded mode no
model reconciles the versions, so the superseded marking matters most there.
