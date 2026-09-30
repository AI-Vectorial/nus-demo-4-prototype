# T1-F5 — Ask, and show it

**Parent:** [T1](T1.md)
**Feature:** F5 ask + UI
**Covers:** REQ-A1, REQ-A2, REQ-A5, REQ-C1, REQ-C2, REQ-U1 .. REQ-U7, REQ-U9 .. REQ-U11
**Status:** `done`

## Done when

In a browser, Q1 shows a cited answer and Q11 shows a refusal that looks different from
an error — epic criteria 21 – 33 pass. Then deploy: criteria 34 – 37.

## Decisions this depends on

- **D7** — how citations are grouped. Three passages from one document as one citation or three — changes what criterion 27 shows and how many `message_citations` rows criterion 23 expects

## Notes

`/history` and `/corpus` are "coming soon" pages in this increment (criterion 33).

## Decisions raised during the build — team, 2026-09-30

- **A — `backend/Dockerfile` copies `corpus/`.** It copied only `app/`, so on Railway the
  refusal (which names the policy owners) would crash and nothing could be indexed. Chose
  **yes**: read-only in the image, never copied to the database (REQ-B5).
- **B — how the Railway index gets filled.** Chose **(a)**: the API indexes an empty
  collection in the background on startup. `/healthz` answers at once (NFR-5); a filled
  collection is left alone; a failure is logged and retried on the next start, so the
  deploy never depends on the model provider. Rejected: `ingest && uvicorn` in the image
  (couples deploy to OpenRouter) and an instructor running it by hand.

## Deviation from the scaffold, following the PRD

`frontend/lib/types.ts` gave the response an `exchange_id`; PRD §5 and criterion 21 say
`conversation_id` + `message_id`. Changed to match the PRD.

## Evidence so far — 2026-09-30

`pytest -q` — 110 passed (`tests/features/test_f5_ask.py`: criteria 11, 16, 21 – 24,
plus `/healthz` with dependencies down and the startup index). `ruff`, `bandit -ll`: clean.
Frontend: `npm run typecheck`, `npm run lint`, `npm run build`: clean.

Live, against the local stack:

```
Q1  answered 10.65s  5 citations        conversation 2ec5b956-…
Q2  answered  4.64s  same conversation: True                       (criterion 24)
Q11 refused  citations []  times 1.34 0.81 0.53 0.76 0.72 s          (criterion 11)
answered times 3.02 3.64 6.86 7.74 9.42 s — p50 6.86 s

stored, conversation 2ec5b956-…                                      (criteria 16, 23)
user       -         -                   -          -      0 citations
assistant  answered  openai/gpt-oss-120b answer-v1  10593  5 citations
user       -         -                   -          -      0 citations
assistant  answered  openai/gpt-oss-120b answer-v1  4591   2 citations
```

**For review:** answered p50 6.9 s locally against NFR-1's 5 s — almost all of it is the
model call. Not one of our criteria; raised, not fixed.

## Criteria 25 – 33 — watched by the team, 2026-09-30

No browser in the Codespace, so these were checked by the team in the Codespace's editor
preview, not asserted in CI. Team reported **"all pass"** for 25 – 33, including:

- Q1 answered with the v3.1 figures (£75 / £500 / £2,500), five citations beneath it, the
  two v3.0 citations labelled **Superseded** in the warning colours (27, 28)
- Q11 → the dashed "Not covered by the policy corpus" box with the four owners (29a)
- `GENERATION_ENABLED=false` → the "No answer could be composed" banner and sections found,
  no answer text (29b)
- API stopped → the solid-red "Error — no answer, and no refusal" box (29c)

## Getting the team a browser that could reach the app — for review

The page's JavaScript called `http://localhost:8000`, which in a browser means the
viewer's own machine. On the team's network `*.app.github.dev` did not resolve at all
(`DNS_PROBE_FINISHED_NXDOMAIN`), and VS Code desktop's forwarding of 8000 did not reach it
either, so every question showed the error state. With the team's agreement: in
development only, the page now calls `/api` on its own origin and `next.config.ts`
forwards it to the API inside the Codespace (`db193dd`). Production is unchanged.

Along the way, Next.js 16's dev server generated `frontend/AGENTS.md` and
`frontend/CLAUDE.md` on its own. Left untracked; not followed; raised for review.

## Still to do

- Deploy (stage 05), then criteria 34 – 37 and the manual criterion 20 on the live URL
  (stage 06).
