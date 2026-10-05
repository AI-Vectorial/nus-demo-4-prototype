# Stage 01 — Shape

**~15 minutes.** Turn the PRD into *your* ticket, with acceptance criteria you wrote.

---

## Inputs

| | |
|---|---|
| `docs/project-brief.md` | why this product exists |
| `docs/PRD.md` | what must be true |
| `docs/features.md` | what to build first |

## Output

`tickets/T1-<short-name>.md`, from `pipeline/templates/ticket.md`.

## The gate

> **The acceptance criteria are written by the team, in the team's words.**

---

# The prompt

```
We are table N.   <- your number

First, before anything else: check which branch we are on. If it is not
work/table-N, create it with `git checkout -b work/table-N` and confirm
it. table-N itself is protected and cannot be pushed to -- everything we
build lands on work/table-N and reaches table-N through a pull request
at stage 05.

Then read docs/project-brief.md, docs/PRD.md and docs/features.md, and
help me shape our first ticket.

Do NOT write acceptance criteria for me. Instead:

1. Summarise in five lines what you believe we are building, so I can
   correct you if you have it wrong.

2. Tell me which requirement IDs from the PRD fall inside F1 to F8.

3. Ask me, one at a time, the questions you need answered to know when
   we are done. After each answer, play it back as a single
   pass-or-fail statement and ask me to confirm the wording.

4. When I confirm we have enough, write:

   tickets/T1.md -- the epic, using pipeline/templates/ticket.md, with
   MY wording in the acceptance criteria.

   tickets/T1-F1-ingest.md through T1-F8-history.md -- one child per
   feature, using pipeline/templates/feature-ticket.md. Each carries its
   requirement ids from features.md, a single pass-or-fail "Done when",
   and the section 10 decisions it depends on. Status starts at todo.
   Mark F6, F7 and F8 as cuttable -- they are the scope we drop if we
   run short.

   The epic holds the acceptance criteria. The children hold the
   tracking -- do not duplicate the criteria into them.

Stop after step 1 and wait for me.
```

---

## Why the agent must not write the criteria

Acceptance criteria written by an agent are a restatement of the PRD. Criteria written
by the team are a statement of what *they* understood — and the difference between those
two is the most useful thing that happens in this stage.

If the team cannot say when the thing is done, **they do not yet know what they are
building**, and finding that out now costs fifteen minutes. Finding it out at the release
gate costs the session.

## What good looks like

**Bad** — a restatement:
> - Ingestion is implemented correctly

**Good** — checkable, and in their words:
> - Running `python -m app.ingest` on an empty collection indexes every document in `backend/corpus/`
> - Running it a second time leaves the passage count unchanged
> - Every passage carries the document title and the section heading it came from
> - Asking "what is the travel approval threshold" returns the Travel and Expense Policy section in the top three results

## Before you leave this stage

- [ ] The ticket exists in `tickets/`
- [ ] Every acceptance criterion is **pass or fail** — no "properly", "correctly", "well"
- [ ] Every criterion names a requirement ID from the PRD
- [ ] The team can read each one aloud and say what they would type to check it
- [ ] Scope is the whole product, **F1–F8, in one increment**
- [ ] **F6, F7 and F8 are marked cuttable.** They are what gives if time runs short — a stage never is
