# M04 — day-of runbook

**Minute by minute. What to say, when to move, what to watch.**

| | |
|---|---|
| **Format** | 5 tables · 150 minutes · one instructor roaming, one on the gate |
| **Companion** | `CV-NUS_M04_Dry_Run_Walkthrough.md` — the depth. This is the timing sheet |

---

# Before anyone sits down

- [ ] Five Codespaces **pre-created and confirmed running**
- [ ] Reference deployment answering — open it in a tab
- [ ] `table-1` … `table-5` at `main`
- [ ] Five printed table cards, numbers written in
- [ ] ⚠️ **No participant has admin** — admins bypass the ruleset, and the ruleset is the module

---

# 0:00 — Open  ·  *5 min*

**Say this. It is the single most important minute of the session:**

> **You are building the whole product — F1 to F8 — and releasing it in one
> pull request at the end.**
>
> **But done is a completed pipeline and a deployed increment. Not a finished
> product.** A team that ships F1 to F5 and cuts the rest has still shaped a
> ticket, defended a plan to a human, reviewed in five passes, written a
> rollback and released through a gate. **That is the module.**
>
> **F6, F7 and F8 are cuttable. The six stages are not.** If you are running
> short: **cut scope, never a stage.**

**Say both halves.** The target is the whole product; the definition of done is
the pipeline. A table that hears only the first half skips the review to reach
F8 — and the review is what is being assessed.

Then: hand out cards, point at the reference URL, say *"that is the target, not
the homework."*

---

# 0:05 — Stage 01 shape  ·  *15 min*

They write a ticket with acceptance criteria **in their own words**.

**Roam and check:** are the criteria theirs, or did the agent write them?

> *"Read me your third acceptance criterion. Now tell me how you would know it
> was false."*

⚠️ **Watch for:** tables that start coding. The plan gate is worthless if the
work is already done. Stop it immediately.

---

# 0:20 — Stage 02 plan  ·  *25 min*  ·  ⚠️ **THE GATE**

The agent presents **every open decision in one block**, then stops. They choose.

**Then you interview. Five questions, five minutes per table:**

| | |
|---|---|
| 1 | *Your plan says chunk size 400. **Why 400?*** |
| 2 | *What happens when the corpus cannot answer?* |
| 3 | *What happens when the model is unreachable?* |
| 4 | *Which part is riskiest, and what if it fails?* |
| 5 | *What are you deliberately not doing?* |

> **Question 1 is the gate.** *"That's what the agent suggested"* → **reject the
> plan.** Send them back to run the decision interview properly.

⚠️ **At least one plan should be genuinely rejected.** M04.3 needs a refusal
that is *checkable, not narrated*. If every plan sails through, the lesson did
not happen. **Be willing to be the one who says no.**

**Timebox hard.** Five tables × 5 minutes = 25. Do not drift.

---

# 0:45 — Stage 03 build  ·  *60 min*

```
F1 ingest ─▶ F2 retrieve ─▶ F3 refuse ─▶ F4 generate ─▶ F5 ask + UI
                                                           │
                  ┌────────────────────────────────────────┘
                  ▼
           F6 follow-up ─▶ F7 corpus ─▶ F8 history       cuttable
```

They can run everything locally — Postgres and Qdrant are in the Codespace.
**Nothing deploys in this stage.** It all goes out at 2:20, after the PR is
approved and merged.

**Say at 1:15 (halfway):** *"Look at where you are and decide what you are
cutting. F8, then F7, then F6. Decide it now and write it down — deciding it at
2:10 means you decided it by running out of time."*

> **The mid-point prompt is about scope, not deployment.** A table that has not
> chosen what to drop by halfway will try to carry all eight into stage 04 and
> arrive with nothing reviewed.

**Roam for:**

| | |
|---|---|
| A table stuck >10 min | go in. Anything longer is a scaffold gap, not their failure |
| Retrieval "not working" | ask what `MIN_SCORE` is and how they chose it |
| **Anyone editing the corpus** | ⚠️ **stop them.** This is the lesson, not a slip |
| Still inside F1–F5 at 1:15 | tell them to cut F6–F8 **out loud and in the ticket** |
| A top bar with buttons that go nowhere | ⚠️ the interface shows what exists. Cut the feature, cut the button |
| A table saying they cannot review yet | **they are not finishing F8 first.** Scope is what gives, never the stage |

---

# 1:45 — Stage 04 review  ·  *25 min*

**First 10 minutes: the warm-up.** `docs/review-example/README.md` — somebody
else's code, tests green, **real defects in it**.

The one that matters is `> 75` where the policy says *"£75 or more"*. Exactly
£75 is auto-approved and nobody ever sees it.

⚠️ **If a table misses it, stop the room and walk through it.** Answers and
grading: `docs/instructor/review-example-answers.md`.

**Remaining 15: the same five passes on their own code.** Every finding gets a
recorded decision — *"noted, not fixing, because…"* is a valid one. An
unrecorded finding is not a review.

---

# 2:10 — Stage 05 release  ·  *10 min*  ·  ⚠️ **THE SECOND GATE**

Release plan **with a rollback written before merge**, then **one PR carrying
everything they built**. Check the description names what they cut.

**Reviewing the PR:** Files changed → Review changes.

| | |
|---|---|
| **Comment** | unlocks nothing — merge stays blocked |
| **Approve** | unlocks the merge |
| **Request changes** | blocks until you explicitly approve later |

⚠️ **Use *Request changes*, not *Comment*, when you mean no.** And
**request-changes does not clear itself** — until you submit an Approve, that
table is blocked however many times they push. **Do not walk away from a table
you have blocked.**

Only **`gate`** is required. Glance at it and move.

---

# 2:20 — Stage 06 verify  ·  *15 min*

The merge happens here, and the deploy with it. Each table then shows three
things on **their own URL**:

1. An answer, with citations
2. **A refusal** — and why that is the product working
3. The cited section, opened in the corpus browser — **or, if they cut F7, what
   they cut and why**

> **A table that cut two features and shipped cleanly has the better run.** Say
> so in front of the room, or the next cohort will hear that eight features is
> the bar.

**Closing question, to every table:**

> *"Where did AI help, where did it displace or risk something, and which
> control caught it?"*

---

# If it goes wrong

**A failed deploy cannot take a site down.** Railway will not route traffic to a
build whose health check never passed. Five separate deployments.

| Red | Do |
|---|---|
| **scope check** | ⚠️ **Do not fix it.** Send them back to revert. This is the lesson |
| backend / frontend | send them back; the agent fixes it |
| deploy | re-run the job — it already retries three times |
| smoke test | build logs → `/healthz` → service variables |

**Nuclear, ~20 seconds:** `./scripts/reset_table.sh 3`

---

# Record while it is fresh

| | |
|---|---|
| How far did each table get, and what did they cut? | **the number that decides everything next time** |
| Did anyone cut a stage to reach a feature? | if so, the 0:00 framing did not land |
| Did the agent stop at the decision interview, or answer itself? | |
| Was a plan genuinely rejected? Did they re-plan or argue? | |
| Where did tables stick, and for how long? | >10 min = fix the scaffold |
| Anything ambiguous in the docs? | fix the doc, not the table |

---

*M04 Runbook · CONFIDENTIAL — CV — NUS AIDF Alliance*
