# Stage 03 — Build

**~60 minutes. The largest stage, and the protected one.**

Build what the approved plan says. Nothing else.

---

## Inputs

**`tickets/T0-alignment.md`** · `tickets/T1.md` · `tickets/T1-F*.md` · `tickets/T1-plan.md` **(approved)**

## Output

Working code, passing tests, committed to `work/table-N`.

## The gate

> **The team's own acceptance criteria pass — run, not asserted.**

---

# The prompt

> **Run it with four words.** Tell your agent:
>
> ```
> Follow the prompt in pipeline/03-build.md
> ```
>
> It reads the block below itself. Pasting it also works — but a paste that loses a
> line is a long way to debug, and an edited prompt reaches every table for free.

```
The plan is approved. Build it.

Do NOT re-plan. Do not re-read the PRD end to end, do not restate the
plan back to me, do not write a build plan of your own. Read
tickets/T0-alignment.md and tickets/T1-plan.md, go to item 1, and write
code.

Work in the order the plan sets out. After each piece: run the tests,
commit, and print ONE status line in exactly this shape --

  [F1 ingest] tests 12/12 ok | ruff ok | commit a1b2c3d | next F2

-- then CONTINUE to the next piece without waiting for me.

Stop and wait only if one of these is true:
  - a test has failed twice and you do not know why
  - you need a dependency we do not already have
  - the plan turns out to be wrong

I am reading the status lines. If I want you to stop, I will say so.

== The one planned stop: when F5 is done ==

F5 is where the product first works end to end. Everything after it --
F6 follow-up, F7 corpus, F8 history -- is cuttable by design.

So when F5 is done, STOP and wait, even though nothing has gone wrong.
Report which features are done, what remains, and anything you are
worried about. Then ask me exactly one question:

  "How far do we go -- F6, F7, F8, or stop here and move to stage 04?"

Do not answer it yourself and do not assume we are continuing. Stopping
at F5 is a normal answer, not a failure: F1 to F5 is a complete product.

Whatever I cut -- here, or at any point if I tell you to cut earlier --
do all four of these, then go no further:

  1. Set that child ticket's Status to cut -- not todo, not done
  2. MOVE its acceptance criteria out of the criteria list in
     tickets/T1.md and into "Out of scope", with my reason. Do not
     leave them sitting in the list unticked. A criterion we chose not
     to meet and a criterion we failed to meet look identical on the
     page and mean opposite things -- one is a decision, the other is
     a gap
  3. Take its action out of the top bar
  4. Commit, with a message saying what was cut and why

A feature left half-built is worse than a feature cut.

Write the test before the code where you reasonably can. Our acceptance
criteria are the specification. Never weaken or skip a test to get a
green build, and take configuration from the environment, not literals.

When a feature is finished, set its child ticket's Status to done and
paste in the one command and its output that show the "Done when" line
is satisfied. A ticket marked done with nothing behind it is a claim,
not a record. Do this as you go -- do not save it all for the end.

Begin.
```

---

## Build order

The feature list is already in dependency order. **Do not reorder it** without saying why.

```
F1 ingest ─▶ F2 retrieve ─▶ F3 refuse ─▶ F4 generate ─▶ F5 ask + UI
                                                            │
                   ┌────────────────────────────────────────┘
                   ▼
            F6 follow-up ─▶ F7 corpus ─▶ F8 history       cuttable
```

**Nothing deploys from this stage.** Building ends with everything committed on
`work/table-N`. It reaches `table-N` through one pull request at stage 05, and it goes
live at stage 06 after a human has approved that pull request — which is the only reason
the gate is worth anything.

**Add each top-bar action when its route lands (REQ-U9).** **Corpus** with F7,
**History** with F8. If a feature is cut, its button is cut too.

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

**The agent stops once on its own, when F5 is done**, and asks how far to go. That is
deliberate: F5 is where the product first works end to end, and everything after it is
the cuttable tail. One stop, at the only point where there is genuinely something to
decide — you should not have to interrupt a running agent to make a decision this
deliberate.

**You can also cut earlier**, at any moment, by saying so. If the clock says you will
not reach F5, cut inside the critical path and say which requirement goes with it.

**Cut from the back: F8, then F7, then F6.** They are cuttable by design. Record the cut
in the ticket as out of scope, take the matching action out of the top bar, and move on
to stage 04 with the time it bought you.

Stopping at F5 with a review, a release plan and a deployment is a **better** outcome
than reaching F8 with none of them. The pipeline is what is being assessed; the features
are only what it is assessed on.

## Before you leave this stage

- [ ] Every acceptance criterion from the ticket passes, **and the team watched it pass**
- [ ] `pytest -q` is green
- [ ] `ruff check` and `bandit -r app/ -ll` are clean
- [ ] No literal model name, URL, dimension or threshold in code
- [ ] The top bar offers **nothing that does not exist** — every action opens a route
- [ ] The cut decision was **taken out loud and answered**, not drifted past
- [ ] Anything cut is written down as cut, not left half-built
- [ ] A cut feature's criteria are **in "Out of scope"** — not unticked in the list
- [ ] Each feature was committed **as it finished**, not all at the end
- [ ] No test was skipped, weakened or deleted to get here
- [ ] `/healthz` reports passages indexed, not zero
- [ ] The evaluation set has been run **against the live index since the last
      change to D0, D1 or D2** — all ten answer, all three refuse
- [ ] Work is committed to `work/table-N` — **and nothing has been deployed**
