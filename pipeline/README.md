# The pipeline

Six stages. Each has one job, one output, and one gate.

```
01 shape ──▶ 02 plan ──▶ 03 build ──▶ 04 review ──▶ 05 release ──▶ 06 verify
  15min        25min        60min        25min          10min         15min
                 │                                                       │
          ⚠️ HUMAN GATE                                          ⚠️ HUMAN GATE
       approve or reject                                      approve, then merge
```

| | Produces | Gate |
|---|---|---|
| **01 shape** | `tickets/T1-*.md` | the team wrote the acceptance criteria |
| **02 plan** | `tickets/T1-plan.md` | ⚠️ **a human approves or rejects** |
| **03 build** | working code | their criteria pass |
| **04 review** | `tickets/T1-review.md` | a decision per finding |
| **05 release** | `tickets/T1-release.md` + a PR | a rollback, written before merge |
| **06 verify** | a live URL | it answers on the deployed application |

## Two rules

**In order. No skipping ahead.** You will often see the whole solution at stage 01.
Write it down and wait. Code written during planning turns the plan review into theatre
— and the plan review is the point.

**The gates are real.** Stage 02 can reject a plan. Stage 06 can refuse a release. Being
sent back is a normal outcome, not a failure.

## If you fall behind

**Cut scope, never a stage.** Stopping at F3 with a review, a release plan and a
deployment beats reaching F5 with none of them.

> **Done is a completed pipeline and a deployed increment — not a finished product.**
