# Stage 05 — Release

**~10 minutes. The rollback is written before the merge, not after.**

---

## Inputs

`tickets/T1-review.md` · a green build on `work/table-N`

## Output

`tickets/T1-release.md` from `pipeline/templates/release-plan.md`, and **one pull
request** into `table-N` carrying the whole product.

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
  - Which features are in it, and which we cut

Then commit everything, push, and open ONE pull request from
work/table-N into table-N:

  git add -A
  git commit -m "T1: <what shipped>"
  git push -u origin work/table-N
  gh pr create --base table-N --head work/table-N \
       --title "T1: <what shipped>" \
       --body-file tickets/T1-release.md

The description should link the ticket, the plan and the review record,
and say which features we cut and why. Cutting F6, F7 or F8 is a
legitimate outcome -- say so plainly rather than apologising for it.

Before you open it: confirm the top bar offers no action whose route we
did not build.

Do not merge, and do not approve it yourself. A human approves -- and it
has to be a different person, because GitHub will not accept an approval
from the account that opened the pull request.
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
work/table-N  ──▶  table-N          everything you built, in one request
```

**One pull request, not one per feature.** The release is the product, so the thing a
human reviews should be the product — a reviewer looking at F5 alone cannot see whether
the interface promises screens that were never built.

> **If `gh` asks you to authenticate**, something is wrong with the Codespace
> rather than with you — tell an instructor. It is installed and signed in
> already, and nobody should be pasting a token anywhere.

**Opening the PR does not deploy.** CI runs the checks, a human approves, and the merge
deploys. **A push never deploys** — if it did, the gate would be bypassable, and the gate
is the point.

## Before you leave this stage

- [ ] The release plan says what is being released, in plain language
- [ ] It says how success is confirmed, and how failure is spotted
- [ ] It names what was cut, and says so plainly
- [ ] The rollback is written as **commands**, not as an intention
- [ ] One PR is open, carrying everything, and it links the ticket, the plan and the review
- [ ] Every top-bar action in the PR opens a route that exists
- [ ] CI is green on the PR
- [ ] **Nobody has merged it**
