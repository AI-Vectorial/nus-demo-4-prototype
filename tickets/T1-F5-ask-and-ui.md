# T1-F5 — Ask, and show it

**Parent:** [T1](T1.md)
**Feature:** F5 Ask, and show it
**Covers:** REQ-A1, REQ-A2, REQ-A5, REQ-C1, REQ-C2, REQ-U1 … REQ-U7, REQ-U9 … REQ-U11
**Status:** `in progress`

## Done when

You can ask in a browser and see a cited answer — and a refusal looks different from an error.

## Decisions this depends on

- **D7** — one citation per section, deduplicated, highest score wins. Grouping by document would lose the section a human checks

## Notes

REQ-U9 is met partly: the top bar carries Reset only. History and Corpus arrive with F8 and F7 — see the epic.

## Evidence so far

**Backend, live** (Postgres, Qdrant, `openai/gpt-oss-120b`, `MIN_SCORE=0.51`), 2026-09-27:

```
=== Q1  answered 3311 ms
 - Travel and Expense Policy v3.1 4.2 Approval thresholds current 0.716
 - Travel and Expense Policy v3.0 4.1 Approval thresholds superseded 0.711
 - ...
=== Can I expense my partner's flight if they travel with me?   refused 1029 ms citations 0
=== What is our policy on cryptocurrency held by clients?       refused 440 ms  citations 0
=== How many days of paid parental leave am I entitled to?      refused 425 ms  citations 0
=== GENERATION_ENABLED=false: degraded answer= None 454 ms, 5 citations
```

Postgres, the same conversation: 8 messages. Each assistant row carries outcome, model,
prompt_version (null on refusals), latency_ms and its citations.

```
$ pytest -q        126 passed, 23 deselected
$ pytest -m live   23 passed
$ ruff check .     All checks passed!
$ npx tsc --noEmit && npx eslint . && npx next build   ok
```

Server-rendered page: top bar with **Reset only**, centred empty state, no dark-mode rules.

**Not yet verified:** asking in a browser and seeing each outcome render. There is no
headless browser in the Codespace, so this needs a person to watch it — which the
stage 03 gate asks for anyway.
