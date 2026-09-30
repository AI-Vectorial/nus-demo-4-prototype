# T1-F4 — Generate

**Parent:** [T1](T1.md)
**Feature:** F4 generate
**Covers:** REQ-G1, REQ-G2, REQ-G3, REQ-G4, REQ-G5, REQ-G6
**Status:** `done`

## Done when

An answer cites only retrieved passages, and with `GENERATION_ENABLED=false` an
answerable question still returns its passages as `degraded` — epic criteria 13 – 19
pass (20 is checked manually at stage 06).

## Decisions this depends on

- **D4** — whether superseded policies are shown, hidden or flagged. Changes what the prompt receives and whether criterion 28 can be exercised
- **D6** — what happens when two policies conflict. Surface both, pick one, or refuse — changes the prompt instruction and possibly the outcome returned

## Evidence — 2026-09-30

`pytest -q tests/features/test_f4_generate.py` — 13 passed (criteria 13 – 19). Full suite: 95.

The prompt is `backend/app/generate/prompts/answer.md` (`version: answer-v1`); the D5
refusal is `prompts/refusal.md` (`refusal-v1`), its list of areas read from the corpus
front matter, current documents only.

Live, `openai/gpt-oss-120b`, figures checked against the corpus text:

| Q | Outcome | Time | What it said | Checked |
|---|---|---|---|---|
| 1 | answered | 6.4s | £75 / £500 / £2,500, cites v3.1 4.2 as current | matches v3.1 4.2 table; the superseded v3.0 passage was retrieved first (0.836) and not used as the answer — D4 working |
| 10 | answered | 4.6s | five years (Outsourcing 6.4) vs seven years (Retention 4.1), "these two current passages conflict", escalate to Group Legal and Group Operational Risk | D6 working — both sides, no choice made |
| 7 | answered | 4.0s | 10% or more (KYC 4.2) | matches; no regulator named (criterion 20 preview) |
| 4 | answered | 6.2s | £300, notes superseded v3.0 said £275 | matches v3.1 / v3.0 tables; D4 "previously" wording |
| 11 | refused | 0.4s | D5 template, four areas and owners, Compliance | no model call |

With `GENERATION_ENABLED=false`: Q1 → `Degraded`, 5 citations · Q11 → `Refused` (criterion 19).

**For review:** answered latency was 4.0 – 6.4 s here; NFR-1 wants p50 under 5 s. Measured
properly through `/ask` in F5. An unreachable model retries `LLM_MAX_RETRIES` times before
degrading, so degraded mode can be slow to arrive.
