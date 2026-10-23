# T1-F4 — Generate

**Parent:** [T1](T1.md)
**Feature:** F4 generate
**Covers:** REQ-G1, REQ-G2, REQ-G3, REQ-G4, REQ-G5, REQ-G6
**Status:** `done`

## What this is

An answer is composed from retrieved passages only, using a versioned prompt file, and the answer records its prompt version, model and latency.
With generation off or the provider down, the passages are returned with no composed answer.

## Done when

With `GENERATION_ENABLED=false`, or with `failing_model`, the output is passages with `answer: null` and `outcome: degraded`, and a successful answer cites only passages it was given.

## How to check it

```bash
cd backend && pytest -q -k "generate or degraded"
```

All generation and degraded tests pass, including the test that `GENERATION_ENABLED=false` returns passages with no model call.

## Decisions this depends on

| | | |
|---|---|---|
| **D4** | whether superseded policies are shown, hidden or flagged | Decides how superseded passages enter the prompt and the citations. |
| **D6** | what happens when two policies conflict | Decides whether the prompt surfaces both conflicting passages or refuses. |

## What this touches

- `backend/app/generate/` (a composition function over `generate()`, not a second SDK import)
- `backend/app/generate/prompts/` (versioned prompt file, new)
- `backend/tests/` generation and degraded tests, using `model` and `failing_model`

## Not in this feature

- The `/ask` endpoint and the turn record (F5)
- Follow-up context (F6)
- Any model call that bypasses `app.generate` (the provider boundary test forbids it)

## Evidence

> ⚠️ **Required before this ticket can be `done`.** Paste the command you ran and
> the output it produced. CI reads this section, and "works" or "tested" does not
> count — it is a claim, not a record. A ticket marked done on a claim is reported
> as not done.

```
```

## Notes

Build the kill switch while writing the model call. Retrofitting it changes every caller.

### Evidence, F4

```
$ cd backend && pytest -q && ruff check .
90 passed, 1 warning in 2.99s
All checks passed!

Live, real model call (anthropic/claude-haiku-5.5), prompt answer_v1:
Q1  Answered  latency_ms=4950  notice: superseded passage retrieved
    Tier table (below £75 / £75 / £500 / £2,500) checked against v3.1 §4.2: present.
Q4  Answered  latency_ms=3802  notice: superseded passage retrieved
    Answer: £300, v3.1 §6.2. Also mentions v3.0 §6.1 (£275), labelled superseded.
```

Degraded mode (GENERATION_ENABLED=false, failing provider) is proven with fakes: passages returned, `answer` null, no model call.

### Limits, stated not hidden

- "Cites only retrieved passages" (Done-when) is enforced by the prompt rule, not by code. Nothing checks the answer's citations against the passages. A stage 04 review item.
- The superseded notice fires when any superseded passage was retrieved, not when the answer relies on one. D4 says "the answer says when a superseded version was the source". That needs citation checking, which is not built. Recorded as a gap for the team; wording was corrected to match what the code knows.
- The `answered` path does not yet carry a `refused` or `degraded` type into `/ask`. That is F5.
