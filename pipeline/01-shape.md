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
Read docs/project-brief.md, docs/PRD.md and docs/features.md.

Then help me shape our first ticket.

Do NOT write acceptance criteria for me. Instead:

1. Summarise in five lines what you believe we are building, so I can
   correct you if you have it wrong.

2. Tell me which requirement IDs from the PRD fall inside F1 to F5.

3. Ask me, one at a time, the questions you need answered to know when
   we are done. After each answer, play it back as a single
   pass-or-fail statement and ask me to confirm the wording.

4. When I confirm we have enough, write:

   tickets/T1.md -- the epic, using pipeline/templates/ticket.md, with
   MY wording in the acceptance criteria.

   tickets/T1-F1-ingest.md through T1-F5-ask-and-ui.md -- one child per
   feature, using pipeline/templates/feature-ticket.md. Each carries its
   requirement ids from features.md, a single pass-or-fail "Done when",
   and the section 10 decisions it depends on. Status starts at todo.

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
- [ ] Scope is F1–F5. **Not F6+**
