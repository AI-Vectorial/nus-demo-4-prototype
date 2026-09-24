# Stage 05 — Release

**~10 minutes. The rollback is written before the merge, not after.**

---

## Inputs

`tickets/T1-review.md` · a green build on `table-N/build`

## Output

`tickets/T1-release.md` from `pipeline/templates/release-plan.md`, and **an open pull
request** into `table-N`.

## The gate

> **A rollback exists, in writing, before anything merges.**

---

# The prompt

```
Write tickets/T1-release.md using pipeline/templates/release-plan.md.

It must answer:
  - What is being released, in one sentence a non-engineer understands
  - How we will know within two minutes that it worked
  - How we will know it did NOT work
  - Exactly how to reverse it, as commands
  - What we cannot reverse, if anything

Then open a pull request from table-N/build into table-N. The
description should link the ticket, the plan and the review record.

Do not merge. A human approves.
```

---

## Why the rollback comes first

A rollback written **after** a release is written by someone who already believes it
worked. Written before, it is written by someone who still thinks failure is possible —
and that is the person you want writing it.

Here it is genuinely simple: revert the merge commit and push. Railway redeploys the
previous version in about ninety seconds. **Write it down anyway.** The discipline is the
deliverable, not the difficulty.

## The pull request

```
table-N/build  ──▶  table-N
```

**Opening the PR does not deploy.** CI runs the checks, a human approves, and the merge
deploys. **A push never deploys** — if it did, the gate would be bypassable, and the gate
is the point.

## Before you leave this stage

- [ ] The release plan says what is being released, in plain language
- [ ] It says how success is confirmed, and how failure is spotted
- [ ] The rollback is written as **commands**, not as an intention
- [ ] The PR is open and links the ticket, the plan and the review
- [ ] CI is green on the PR
- [ ] **Nobody has merged it**
