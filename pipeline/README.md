# The pipeline

Six stages. Each has one job, one output, and one gate.

```
01 shape ──▶ 02 plan ──▶ 03 build ──▶ 04 review ──▶ 05 release ──▶ 06 verify
  15min        20min        60min        20min          10min         15min
                 │                                                       │
          ⚠️ HUMAN GATE                                          ⚠️ HUMAN GATE
       approve or reject                                      approve, then merge
```

| | Produces | Gate |
|---|---|---|
| **01 shape** | `tickets/T0-alignment.md`, then `tickets/T1-*.md` | a human corrected the alignment, and the team wrote the acceptance criteria |
| **02 plan** | `tickets/T1-plan.md` | ⚠️ **a human approves or rejects** |
| **03 build** | working code | their criteria pass |
| **04 review** | `tickets/T1-review.md` | a decision per finding |
| **05 release** | `tickets/T1-release.md` + **one PR, the whole product** | a rollback, written before merge |
| **06 verify** | a live URL | it answers on the deployed application |

## Running a stage

You do not paste prompts. Open the stage file, read it, then tell your agent:

```
Follow the prompt in pipeline/01-shape.md
```

**Read the stage file anyway.** The checklist at the bottom of each one is yours, not
the agent's, and nothing downstream checks it for you.

## Two rules

**In order. No skipping ahead.** You will often see the whole solution at stage 01.
Write it down and wait. Code written during planning turns the plan review into theatre
— and the plan review is the point.

**The gates are real.** Stage 02 can reject a plan. Stage 06 can refuse a release. Being
sent back is a normal outcome, not a failure.

## If you fall behind

**Cut scope, never a stage.** F6, F7 and F8 are the scope — drop them from the back.
Stopping at F5 with a review, a release plan and a deployment beats reaching F8 with
none of them.

> **Done is a completed pipeline and a deployed increment — not a finished product.**
