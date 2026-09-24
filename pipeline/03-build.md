# Stage 03 — Build

**~60 minutes. The largest stage, and the protected one.**

Build what the approved plan says. Nothing else.

---

## Inputs

`tickets/T1-*.md` · `tickets/T1-plan.md` **(approved)** · `docs/PRD.md`

## Output

Working code, passing tests, committed to `table-N/build`.

## The gate

> **The team's own acceptance criteria pass — run, not asserted.**

---

# The prompt

```
The plan is approved. Build it.

Work in the order the plan sets out. After each piece:
  - run the tests
  - show me what passed and what did not
  - commit, with a message saying what changed and why

Write the test before the code where you reasonably can. Our acceptance
criteria are the specification.

Rules:
  - Stop and ask before adding any dependency
  - Stop and ask if the plan turns out to be wrong
  - Never weaken or skip a test to get a green build
  - Configuration comes from the environment, not from literals

Start with the first item in the plan.
```

---

## Build order

The feature list is already in dependency order. **Do not reorder it** without saying why.

```
F1 ingest ──▶ F2 retrieve ──▶ F3 refuse ──▶ F4 generate ──▶ F5 ask + UI
```

**Deploy as soon as F5 works.** A deployed increment completes the pipeline; an
undeployed improvement completes nothing.

## Three places this usually goes wrong

**Ingestion is not idempotent.** REQ-I4 says running it twice changes nothing. Test it by
actually running it twice and comparing counts. A stable passage id — a hash of document,
section and text — makes it fall out for free.

**Refusal is an empty list.** If `retrieve()` returns `list[Hit]`, something will
eventually call the model with an empty list and get a confident invention. Return
`Grounded | Insufficient` and the failure becomes impossible rather than unlikely.

**The kill switch gets postponed.** REQ-G6 is part of F4, not later polish. Build it while
writing the model call — once every caller assumes an answer exists, adding degraded mode
means changing all of them.

## When time runs short

**Say so, and cut scope — never cut a stage.**

Stopping at F3 with a review, a release plan and a deployment is a **better** outcome than
reaching F5 with none of them. The pipeline is what is being assessed.

## Before you leave this stage

- [ ] Every acceptance criterion from the ticket passes, **and the team watched it pass**
- [ ] `pytest -q` is green
- [ ] `ruff check` and `bandit -r app/ -ll` are clean
- [ ] No literal model name, URL, dimension or threshold in code
- [ ] No test was skipped, weakened or deleted to get here
- [ ] Work is committed to `table-N/build`
