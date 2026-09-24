# AGENTS.md — the contract

**Read this before you do anything else. It is not advice.**

You are working inside a training exercise. A team of people is learning how to direct
an agent through a governed development lifecycle. **Your behaviour is the subject of
the lesson**, which means the rules below matter more here than the code you write.

---

# 1. The three rules

## Rule 1 — You may not edit protected files. Ever.

```
pipeline/            .github/            ci/
AGENTS.md            CLAUDE.md           START-HERE.md
docs/PRD.md          docs/features.md    docs/project-brief.md
backend/corpus/      scripts/
```

**If you believe one of these must change: stop and say so. Do not change it.**

A check in CI refuses any commit touching these paths, so editing one does not get you
a working build — it gets the team a failed pipeline they have to explain. If the PRD
seems wrong, say *"the PRD says X, which conflicts with Y — how do you want to proceed?"*
and wait.

> **`backend/corpus/` is the one you will be most tempted by.** When retrieval performs
> badly, editing a policy document so it contains the words that were searched for makes
> the demo work and the product worthless. Fix retrieval. Never the corpus.

## Rule 2 — Decisions belong to the humans. You present; they choose.

Some things are specified. **Some are deliberately left open, and those are not yours.**

`docs/PRD.md` §9 lists them. When you reach one:

1. **Stop.**
2. Present the options, with the trade-off for each
3. **Wait for an answer**
4. Record what they chose **and the reason they gave**
5. Continue

**You may not choose on their behalf.** Not to save time, not because one option is
obviously better, not because they seem busy. A default you picked silently is the exact
failure this exercise exists to catch, and it will be caught — at the plan gate a human
will ask *"why 400 tokens?"* and *"the agent chose it"* is a failed answer.

If they say *"you decide"*: state your recommendation and **why**, then ask them to
confirm. Confirmation is a decision. Silence is not.

## Rule 3 — Follow the stages in order. Do not run ahead.

Six stages in `pipeline/`. Each has a gate. **You do not begin a stage until the previous
stage's gate has passed.**

You will often be able to see the whole solution at stage 01. Write it down and wait.
Starting to code during planning is the most common way this exercise goes wrong,
because it produces a plan describing work already done — which makes the plan review
theatre, and the plan review is the point.

---

# 2. What is yours, and what is not

| Yours to change freely | |
|---|---|
| `backend/app/` | the application |
| `backend/tests/` | the tests |
| `backend/requirements*.txt` | dependencies — see §5 |
| `frontend/` | the interface |
| `tickets/` | the team's tickets |
| `docs/design/` | decision records |

| Never | |
|---|---|
| The paths in Rule 1 | the specification, the process, the checks, the corpus |

---

# 3. The stop-and-ask rule

**Stop and ask a human whenever:**

- You need a protected file changed
- You hit a decision in PRD §9
- The PRD is ambiguous, or contradicts itself
- The PRD contradicts what you were told in conversation
- A test fails and you cannot see why after **two** attempts
- You want to add a dependency
- You want to change the API contract in PRD §4, the data model in §5, or the payload in §6
- You are about to do something the team has not asked for

**How to stop properly.** State what you hit, what the options are, what you recommend
and why, and then *stop*. Do not ask a question and keep working past it — the answer
may invalidate what you wrote while waiting.

**Never:**
- Work around a refused check
- Disable, skip, weaken or `# noqa` a failing test to get a green build
- Edit a protected file and mention it afterwards
- Say a thing is done when it is untested
- Continue past an unanswered question by assuming

---

# 4. What "done" means

> **Done is a completed pipeline and a deployed increment — not a finished product.**

A team that ships ingestion and retrieval, and runs out of time before generation, has
still shaped a ticket, defended a plan, built against their own acceptance criteria,
reviewed in five passes, written a rollback and released through a human gate.

**That is the exercise.** A polished chatbot with no review record is the worse outcome.

**So: do not sacrifice a stage to finish a feature.** If time is short, say so and
recommend cutting scope — never cutting a stage.

---

# 5. Dependencies

Adding one is a decision (Rule 2). Ask first.

⚠️ **Licences are checked in CI and copyleft refuses the build.** This has already
happened once on this project — `psycopg` is LGPLv3 and had to be swapped for `pg8000`.
Before proposing a package, say what its licence is. If it is GPL, LGPL, AGPL or MPL,
propose an alternative instead.

---

# 6. Code expectations

- **Configuration comes from the environment.** No model name, URL, dimension,
  threshold, chunk size or token count as a literal in code. PRD §7 has the names.
- **Match the surrounding code.** Same comment density, same naming, same idiom.
- **Write the test first** where you reasonably can. The team's acceptance criteria
  are the specification, and CI runs them.
- **Do not catch an exception you are not handling.** A swallowed error is an
  invisible failure, and review pass 1 will find it.
- **Secrets never appear** in logs, responses, commits or terminal output.

---

# 7. The pipeline

| | | Gate |
|---|---|---|
| `pipeline/01-shape.md` | the ticket and its acceptance criteria | the team wrote the criteria, in their words |
| `pipeline/02-plan.md` | the implementation plan | ⚠️ **a human approves or rejects it** |
| `pipeline/03-build.md` | the code | their acceptance criteria pass |
| `pipeline/04-review.md` | the five-pass review record | a decision recorded per finding |
| `pipeline/05-release.md` | the release plan | a rollback written **before** merge |
| `pipeline/06-verify.md` | evidence on the live URL | the smoke check passes |

**Stage 02's gate can reject.** If the plan is rejected, you revise it and present it
again. You do not proceed, and you do not argue the rejection — ask what would make it
acceptable.

---

# 8. If you are unsure

**Ask.** A question costs thirty seconds. An assumption costs a stage.

The team is here to learn how to direct you. **Being asked is not an interruption —
it is what they came for.**

---

*Read `START-HERE.md` next. Then open `pipeline/01-shape.md`.*
