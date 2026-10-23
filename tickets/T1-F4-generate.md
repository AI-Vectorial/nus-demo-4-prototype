# T1-F4 — Generate grounded answers

**Parent:** [T1](T1.md)
**Feature:** F4 Generate
**Covers:** REQ-G1, REQ-G2, REQ-G3, REQ-G4, REQ-G5, REQ-G6
**Status:** `done`
**Cuttable:** No

## What this is

Compose policy answers from supported passages and keep the prompt versioned.
If generation is off or the provider fails, return the passages without a composed answer.

## Done when

Pass when supported answers remain grounded and generation-off or provider-failure paths return useful degraded results.

## How to check it

```bash
cd backend && pytest -q tests/features/test_generation.py
```

Pass: tests cover grounding, prompt and answer metadata, the kill switch and a failing provider.

## Decisions this depends on

| | | |
|---|---|---|
| **D4** | Treatment of superseded policies | Which passages may support generation and how their status affects the answer changes. |
| **D6** | Handling conflicting policies | The answer must follow the team's chosen behavior when current policies conflict. |

## What this touches

`backend/app/generate/`, its versioned prompt file and the F4 orchestration path; tests go under `backend/tests/features/`.
Use the existing provider boundary and `ProviderError` rather than importing another provider SDK.

## Not in this feature

Retrieval and refusal decisions belong to F2 and F3.
The `/ask` route, persistence and UI rendering belong to F5.

## Evidence

> ⚠️ **Required before this ticket can be `done`.** Paste the command you ran and
> the output it produced. CI reads this section, and "works" or "tested" does not
> count — it is a claim, not a record. A ticket marked done on a claim is reported
> as not done.

```
cd backend && pytest -q tests/features/test_generation.py tests/features/test_refusal.py tests/features/test_retrieval.py tests/features/test_ingest.py tests/regression/test_provider_boundary.py tests/regression/test_retrieval_contract.py
25 passed, 1 warning in 1.92s
```

## Notes

The fake-provider tests prove the enabled, disabled and provider-failure branches without network access.
