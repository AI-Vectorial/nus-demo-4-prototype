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
backend/corpus/      scripts/            docs/table-card.md
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

`docs/PRD.md` §10 lists them. When you reach one:

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

**Ask once. Then take the answer.**

If they accept your recommendations, play the whole set back one time — *"here is what
we are going with; correct anything, or say go"* — and on "go", **go**. Write your own
reason into the record as the reason, marked as accepted: *"accepted the recommendation:
400 keeps a policy clause whole in one chunk."*

**Do not then ask them to justify it.** Not per decision, not "can you say why", not "are
you sure". They answered. A second pass asking for reasoning they have already delegated
to you is not diligence — it is the same question wearing a different hat, and it burns a
stage they cannot get back.

The record needs a reason beside every value. It does not need the human to have typed
it. What fails at the gate is a blank cell or a value nobody will stand behind — **not
the fact that you suggested it first.**

**Asked for a recommendation, give one.** Plainly — *"I would use 400, because…"* — not
a neutral list with the answer withheld. Refusing to recommend is not neutrality, it is
unhelpfulness wearing its coat. A recommendation is not a decision; it becomes one when
a human says yes.

**And do not ask who anyone is.** Never ask for a reviewer's name, an approver's name or
who is on the team. Approval here is a *role*, not a person: **the team decides, and a
human approves.** Write "the team" or "the release manager" and move on. A question
whose answer changes nothing about what you build is a question not worth the minute.

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
- You hit a decision in PRD §10
- The PRD is ambiguous, or contradicts itself
- The PRD contradicts what you were told in conversation
- A test fails and you cannot see why after **two** attempts
- You want to add a dependency
- You want to change the API contract in PRD §5, the data model in §6, or the payload in §7
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

**That rule is about packages you are proposing to add — a direct dependency, chosen.**

A **transitive** dependency is different. Nobody chose `certifi`; it arrived underneath
something else. You cannot swap it without swapping its parent, so "propose an
alternative" is not advice anyone can act on. For a transitive licence finding, say:

- which package, which licence, and **what pulled it in**
- whether it ships to users or stays in the build
- that the realistic options are **accept with a reason** or **drop the parent**

Then let the team pick. **An `UNKNOWN` licence is a missing fact, not a violation** —
say that it could not be determined and what you would check, rather than reporting it
as a problem found.

---

# 6. Code expectations

- **Configuration comes from the environment.** No model name, URL, dimension,
  threshold, chunk size or token count as a literal in code. PRD §8 has the names.
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

## Check before you assert

**Do not state as fact anything you have not looked at.** *"All dependencies are
permissive"* is a claim about every line of a lockfile — so either read it, or say
*"I have not checked every transitive dependency"*. The second is honest and costs
nothing. The first forces a correction, and a correction costs the reader their
confidence in everything else you said.

This matters most in the stage 04 review, where a confident wrong finding sends a team
off to fix something that was never broken, with the clock running.

## And when you are wrong, be brief about it

Correct it in one line and carry on. **Do not narrate the correction** — no *"this is a
correction to my earlier review, I said X but that was too strong, in fact…"*. Say the
right thing, once, and move. A paragraph of self-revision tells the reader nothing they
can act on and buries the finding underneath it.


---

# 9. The labels, and what each one means

Five different things in this repository are numbered, and mixing them up makes a
sentence impossible to follow. **"F11 needs the team"** reads as *Audit export* to anyone
holding the feature list.

| | Means | Lives in | Example |
|---|---|---|---|
| **`REQ-*`** · `NFR-*` | a requirement | `docs/PRD.md` §4 | `REQ-C5` retrieval runs every turn |
| **`F1`–`F8`** | a **feature** you build | `docs/features.md` | `F3` refuse |
| `F9`–`F12` | features **beyond** the critical path | `docs/features.md` | `F11` audit export |
| **`D0`–`D9`** | a **decision that is the team's** | `docs/PRD.md` §10 | `D2` the refusal threshold |
| **`FND-1`…** | a **finding** from the stage 04 review | `tickets/T1-review.md` | `FND-3` secret in a log line |
| `S1`–`S4` | a success measure | `docs/project-brief.md` | |

**Never reuse `F` for a review finding.** It is the one collision that actually happens,
and it turns a clear review into a puzzle.

When you name one, name it the way the reader can follow: *"`D2` — the refusal
threshold"*, not *"decision 2"*. The label and the thing, together, once.

---

*Read `START-HERE.md` next. Then open `pipeline/01-shape.md`.*
