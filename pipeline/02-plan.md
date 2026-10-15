# Stage 02 — Plan

**~25 minutes, and this is the stage the module is built around.**

The agent proposes. **A human decides.** Some of those decisions are handed to the team
on purpose, and the gate is where they defend them.

---

## Inputs

| | |
|---|---|
| **`tickets/T0-alignment.md`** | **read this first — it is already corrected** |
| `tickets/T1-*.md` | the ticket from stage 01 |
| `docs/PRD.md` §4–§7 | the fixed contracts |
| **`docs/PRD.md` §10** | **the decisions that are yours** |

## Output

`tickets/T1-plan.md`, from `pipeline/templates/plan.md`.

## The gate

> ⚠️ **A human — the release manager — approves or rejects this plan.**
>
> **A rejection is a normal outcome, not a failure.** If the plan is rejected, revise it
> and present it again. Building does not start until it is approved.

---

# Part A — the decision interview

**This happens before any plan is written.**

> **Run it with four words.** Tell your agent:
>
> ```
> Follow the prompt in pipeline/02-plan.md
> ```
>
> It reads the block below itself. Pasting it also works — but a paste that loses a
> line is a long way to debug, and an edited prompt reaches every table for free.

```
Read tickets/T0-alignment.md first. It is the corrected statement of what we
are building and where things live -- use it instead of re-reading the PRD,
the brief and the feature list end to end.

Before you write a plan, run the decision interview.

docs/PRD.md section 10 lists the TEN decisions, D0 to D9, that are
deliberately left to us.
For EACH one, in a single message, give me:

  - the decision, in one line
  - two or three concrete options
  - the trade-off for each option, in one line
  - your recommendation, and why

Then STOP and wait for my answers. All of them, in one block -- do not
ask them one at a time, and do not start the plan until I have replied.

You may not choose any of these for me. If I say "you decide", or I
accept your recommendations, do this and nothing more:

  - play the full set back ONCE, numbered: the decision, the value, and
    your one-line reason for each
  - ask exactly one question: "correct anything, or say go"
  - on "go", write the plan

Then stop asking. Do not walk back through them one by one, do not ask
me to justify any of them, do not ask "are you sure". I answered. Put
YOUR reason in the Why column, marked as accepted -- "accepted: 400
keeps a policy clause whole in one chunk" -- and move on. A blank cell
fails the gate. A reason I agreed to does not.

Present the decisions and stop. Do not preface them by telling me what
you have or have not decided, and do not explain the rules back to me
-- I wrote them. Just the list.
```

**The agent must not proceed past this point without answers.** If it writes a plan
containing a chunk size nobody was asked about, **that is a finding** — raise it at the
gate, out loud, because it is the exact failure the exercise exists to surface.

## The decisions

From PRD §10 — the embedding model and its dimensions · chunk size and overlap · the
refusal threshold and how it was chosen · how many passages to retrieve · superseded
policies · what a refusal says · **what happens when two policies conflict** · citation
grouping · **how much conversation a follow-up sees** · **whether a follow-up
re-retrieves**.

> **Two of those bite hardest.** The embedding dimension fixes the Qdrant collection at
> creation, so changing it later means re-indexing. And REQ-C5 requires retrieval to run
> on *every* turn — skipping it on a follow-up gives a confident answer from the previous
> question's passages, which looks right and is not.

> **Every answer goes into configuration, not into code.** PRD §8 has the names. A value
> the team chose should be visible in one file, not buried in three.

---

# Part B — the plan

```
Now write tickets/T1-plan.md using pipeline/templates/plan.md.

It must include:
  - the decisions I gave you, with MY reasons recorded next to each
  - the files you will create or change, and what each one does
  - the order you will build in, and why that order
  - what you will NOT do
  - the riskiest part, and what you will do if it does not work

Keep it to one page. I have to read it and decide.

When you are done, commit what this stage produced to work/table-N:

  git add tickets/
  git commit -m "02 plan: the decisions, and why we made them"

Commit at the end of every stage. A Codespace that dies at 1:30 with
four stages of uncommitted work costs the session; the same crash with
four commits behind it costs nothing.
```

---

## What the release manager asks

Five questions. **Be ready to answer without opening the code.**

| | |
|---|---|
| 1 | *Your plan says chunk size 400. **Why 400?*** |
| 2 | *What happens when the corpus cannot answer the question?* |
| 3 | *What happens when the model is unreachable?* |
| 4 | *Which part is riskiest, and what do you do if it fails?* |
| 5 | *What are you deliberately not doing?* |

> **Question 1 is the one that matters.** If the answer is *"that's what the agent
> suggested"*, the plan is rejected and the team runs the decision interview properly.
> That is not a punishment — it is the lesson, and it lands better when it actually
> happens to somebody.

## Before you leave this stage

- [ ] Every PRD §10 decision has an answer **and a human's reason**
- [ ] The plan fits on one page
- [ ] It names the riskiest part
- [ ] It says what is **not** being done
- [ ] ⚠️ **A human has approved it — recorded in the ticket, with a timestamp**
- [ ] The plan is **committed to `work/table-N`**
- [ ] **No code has been written yet**
