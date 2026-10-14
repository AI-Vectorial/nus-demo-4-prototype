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

| | |
|---|---|
| `tickets/T0-alignment.md` | from `pipeline/templates/alignment.md` — **written first** |
| `tickets/T1.md` + `T1-F1..F8` | from `pipeline/templates/ticket.md` and `feature-ticket.md` |

## The gate

> **A human has corrected the alignment document, and the acceptance criteria are
> written by the team, in the team's words.**

---

# The prompt

> **Run it with four words.** Tell your agent:
>
> ```
> Follow the prompt in pipeline/01-shape.md
> ```
>
> It reads the block below itself. Pasting it also works — but a paste that loses a
> line is a long way to debug, and an edited prompt reaches every table for free.

```
We are table N.   <- your number

First, before anything else: check which branch we are on. If it is not
work/table-N, create it with `git checkout -b work/table-N` and confirm
it. table-N itself is protected and cannot be pushed to -- everything we
build lands on work/table-N and reaches table-N through a pull request
at stage 05.

== Part A -- alignment, before any ticket ==

Read docs/project-brief.md, docs/PRD.md and docs/features.md, then look
over the repository as it stands. Write tickets/T0-alignment.md using
pipeline/templates/alignment.md. Fill in every section, in your own
words, including where things live in this scaffold and the commands
that run it.

List the PRD section 10 decisions under "Still open" and leave every one
of them unanswered. You do not decide these. If you find yourself
needing one of them to continue, say so and stop.

Then STOP and ask me to read it and correct it. Do not write any ticket
until I have.

== Part B -- the ticket ==

Once I have corrected the alignment document:

1. Tell me which requirement IDs from the PRD fall inside F1 to F8.

2. Ask me, in ONE message, every question you need answered to know
   when we are done. Number them. Do not ask them one at a time, and
   do not answer any of them yourself.

3. When I reply, write all the criteria back as a numbered list of
   pass-or-fail statements, in MY words, and ask me once:
   "correct any of these, or say go."

4. On "go", write:

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

Write all of step 4 in one pass. Do not stop between tickets.
```

---

## Why there is an alignment document before the ticket

It costs about two minutes and it buys three things.

**It is the cheapest gate in the session.** A human reads five lines at minute three and
says *"no, that is not what we are building"* — before a ticket, a plan or a line of code
has been written on top of the misunderstanding.

**Stages 02 to 06 read it instead of re-reading the repository.** One short corrected file
is faster than three long ones, and on a slow agent that difference is minutes per stage.

**It records what has *not* been decided.** The ten §10 decisions are listed and left
blank on purpose. If a value for one of them later turns up in the plan, you can see
exactly where it came from — which is the finding stage 02's gate exists to produce.

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

- [ ] `tickets/T0-alignment.md` exists, and **a human corrected something in it**
- [ ] Its "Still open" list has all ten §10 decisions, **all still blank**
- [ ] The ticket exists in `tickets/`
- [ ] Every acceptance criterion is **pass or fail** — no "properly", "correctly", "well"
- [ ] Every criterion names a requirement ID from the PRD
- [ ] The team can read each one aloud and say what they would type to check it
- [ ] Scope is the whole product, **F1–F8, in one increment**
- [ ] **F6, F7 and F8 are marked cuttable.** They are what gives if time runs short — a stage never is
