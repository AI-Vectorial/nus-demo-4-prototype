# Fast path — every prompt and every answer, ready to paste

⚠️ **INSTRUCTOR AND DRY-RUN ONLY. Do not give this to a table.**

The slow part of this lab *is* the lab. Deciding chunk size, defending a
threshold, choosing what happens when two policies contradict each other —
that is the thing being taught. This file skips all of it, which is exactly
what a table must not do.

**Use it to:** prove the machinery works, rehearse, or demo end to end.

---

# 0 · Ready  ·  *1 min*

```bash
./scripts/quickstart.sh 3
```

Checks the branch, the key, both stores, the frontend and the agent. Creates
`work/table-3` if you are on `table-3`. **Refuses to continue if anything is
wrong**, because all of these break later, further from the cause.

Then:

```bash
claude
```

---

# 1 · Shape  ·  *~4 min*

### Paste

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
   feature, using pipeline/templates/feature-ticket.md.

   The epic holds the acceptance criteria. The children hold the
   tracking -- do not duplicate the criteria into them.

Stop after step 1 and wait for me.
```

### 👀 Check the summary mentions **refusal**

If it does not, that is a finding — the build will drift toward a chatbot that
never declines.

### Then paste — this answers step 3 in one go

```
Summary is correct.

Answers to everything you need for the acceptance criteria:

- An answer arrives in under 5 seconds; a refusal in under 1.5, because
  a refusal makes no model call and should be visibly faster.
- Citations are always visible without clicking anything.
- A claim of exactly 75 pounds requires approval -- thresholds are
  inclusive.
- A superseded citation is visibly marked as superseded.
- With generation off, the passages still come back, clearly flagged.
- The top bar carries Reset only in this slice. History and Corpus
  arrive with F8 and F7. We do not ship buttons that do nothing.
- Put NFR-2, NFR-3 and NFR-5 in as criteria. Leave NFR-1, NFR-4 and
  NFR-6 out -- we verify those, they are not criteria for this ticket.

That is enough. Write the epic and the five children.
```

---

# 2 · Plan  ·  *~5 min*

### Paste

```
Before you write a plan, run the decision interview.

docs/PRD.md section 10 lists decisions that are deliberately left to us.
For EACH one, in a single message, give me:

  - the decision, in one line
  - two or three concrete options
  - the trade-off for each option, in one line
  - your recommendation, and why

Then STOP and wait for my answers. All of them, in one block -- do not
ask them one at a time, and do not start the plan until I have replied.

You may not choose any of these for me. If I say "you decide", give me
your recommendation and ask me to confirm it.

Present the decisions and stop. Do not preface them by telling me what
you have or have not decided, and do not explain the rules back to me
-- I wrote them. Just the list.
```

### ⚠️ This is the moment that matters

| | |
|---|---|
| ✅ | Ten decisions in one message, options and trade-offs, **then it waits** |
| ❌ | It picks for you · asks one at a time · starts planning |

**On a dry run, a failure here is the most valuable thing you will find.**
Capture it verbatim.

### Then paste — the tuned values, with reasons

*These are the reference build's settings, measured. Safe to use.*

```
D0  text-embedding-3-small, 1536 dimensions.
    Verified working. 3072 doubles cost and storage for a five-document
    corpus that is not hard to search. Re-indexing later is one command.

D1  Section-first, 400 tokens max, 60 overlap.
    Policy is already written in numbered sections, and a citation to
    "4.2 Approval thresholds" is something a human can verify. Only a
    section over 400 splits, on paragraph boundaries.

D2  MIN_SCORE 0.35, tuned against EVALUATION.md.
    Set below the lowest true answerable score rather than midway to the
    refusals, because the model is a second line of defence -- it
    declines when passages do not answer. A threshold set to catch
    everything refuses valid rephrasings.

D3  Six passages.
    Enough for an answer spanning two sections; few enough that the
    weakest is still relevant.

D4  Show superseded, flagged loudly.
    The corpus indexes them so "has this changed?" is answerable. An
    answer citing a withdrawn policy is the failure we exist to prevent,
    so it has to be impossible to miss.

D5  Say what is not covered, and name the owning team.
    "I don't know" leaves the user where they started. Every document
    names an owner in its front matter.

D6  Surface both, name the conflict, do not resolve it.
    The retention/outsourcing conflict is a governance problem Aldermere
    already has. Resolving it in code makes our software decide which
    policy wins.

D7  One citation per section, deduplicated, highest score wins.
    Grouping by document would lose the section, which is the part a
    human can check.

D8  Five turns of context.
    Enough for "and what about above 500?" to resolve; more starts
    dragging answers toward earlier topics.

D9  Yes, re-retrieve every turn -- on the conversation, not the fragment.
    "And above 500?" needs a different row of the same table, so reusing
    the previous passages answers confidently from the wrong section. But
    embedded alone that fragment matches nothing, so the query carries
    the earlier user turns.
```

### Then

```
Now write tickets/T1-plan.md using pipeline/templates/plan.md.

It must include:
  - the decisions I gave you, with MY reasons recorded next to each
  - the files you will create or change, and what each one does
  - the order you will build in, and why that order
  - what you will NOT do
  - the riskiest part, and what you will do if it does not work

Keep it to one page. I have to read it and decide.
```

Skim it, then:

```
The plan is approved.
```

---

# 3 · Build  ·  ⏱️ *stopwatch on*

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

When a feature is finished, before starting the next one: set its child
ticket's Status to done and paste in the output that shows its "Done
when" line is satisfied.

Start with the first item in the plan.
```

### 📊 Stop the clock when F1 passes

```bash
cd backend && python -m app.ingest      # ~107 passages
python -m app.ingest                    # again: 0 new -- REQ-I4
pytest -q
```

**F1 is roughly a quarter of the build phase.** If it took 25 minutes, sixty for
F1–F5 is not real — and the fix is a more generous scaffold, never a compressed
pipeline.

---

# 4 · Review  ·  *~6 min on the fast path*

```
Review pass 1 of 5: CORRECTNESS only.

Read docs/review-example/expense_rules.py against
backend/corpus/travel-expense-policy-v3.1.md section 4.2.

For each finding: what is wrong, the exact input that shows it, and what
the policy says instead. Do not fix anything. Do not comment on style,
security or naming -- later passes cover those.
```

**It must find `> 75` where the policy says "£75 or more".** Answers and grading:
`docs/instructor/review-example-answers.md`.

Then, on the real code:

```
Now the same five passes on OUR diff, one pass per message.
Record every finding in tickets/T1-review.md with a decision against
each -- including the ones we are not fixing, and why.

Start with pass 1: correctness.
```

---

# 5 · Release and verify  ·  *~8 min*

```
Write tickets/T1-release.md using pipeline/templates/release-plan.md.
It must state the rollback BEFORE we merge. Then commit everything and
push work/table-3.
```

```bash
gh pr create --base table-3 --head work/table-3 \
  --title "T1: the policy assistant" --fill
```

Four checks run. **Nothing deploys.** Approve, merge, then:

```bash
curl -s https://api-table-3-production.up.railway.app/healthz
```

Open **`https://web-table-3-production.up.railway.app`** and ask:

| | |
|---|---|
| *"What is the approval threshold for a travel expense claim?"* | an answer, cited |
| *"Can I expense my partner's flight if they travel with me?"* | **a refusal** |

---

# 6 · Put it back

```bash
./scripts/reset_table.sh 3
git fetch origin && git log origin/table-3 --oneline -1     # matches main
```

---

# Record these

| | |
|---|---|
| 📊 **Minutes for F1** | the number that decides the timings |
| ⚠️ **Did the agent stop at the decision interview?** | or decide for you |
| Anything ambiguous in a stage file | fix the doc, not the table |
| Anything that cost more than ten minutes | a scaffold gap |

---

*M04 · Instructor material · not for participants*
