# Review warm-up — five passes on somebody else's code

**Ten minutes, at the start of stage 04. Before you review your own work.**

`expense_rules.py` was submitted for review. It implements **Travel and Expense
Policy v3.1 §4.2**, which is in `backend/corpus/travel-expense-policy-v3.1.md`.

`test_expense_rules.py` **passes.** Every test is green.

---

## Why warm up on this

Reviewing your own code is hard: you already believe it works, because you just
watched it work. This is somebody else's, it is short, and **it contains real
defects** — so the five passes have something to find, and you find out what
finding something feels like before you turn the method on yourself.

**Do not run the tests first.** They pass. That is the point.

---

## The five passes

Give your agent the file and take one pass at a time. **One pass per prompt** —
asked for everything at once, an agent returns a shallow list of all five.

| | Pass | Ask |
|---|---|---|
| 1 | **Correctness** | Does it do what the policy says? Check the boundaries against §4.2 |
| 2 | **Security** | Anything exploitable, or any credential or secret exposed? |
| 3 | **Data and privacy** | What does it record, where does that go, and should it? |
| 4 | **Dependencies** | Anything added, and may we ship it? |
| 5 | **Maintainability** | Will the next person understand and safely change this? |

### A prompt that works

```
Review pass 1 of 5: CORRECTNESS only.

Read docs/review-example/expense_rules.py against
backend/corpus/travel-expense-policy-v3.1.md section 4.2.

For each finding: what is wrong, the exact input that shows it, and what the
policy says instead. Do not fix anything. Do not comment on style, security or
naming -- later passes cover those.
```

Then the same shape for passes 2 to 5.

---

## Record every finding

Use `tickets/T1-review.md`. **Every finding gets a decision**, including the
ones you choose not to act on — *"noted, not fixing, here is why"* is a
perfectly good review outcome, and an unrecorded one is not a review at all.

| # | Pass | Finding | Severity | Decision |
|---|---|---|---|---|
| 1 | | | | |

---

## Two things this is testing

**Passing tests are not evidence of correct behaviour.** They are evidence that
the cases somebody thought of behave as that person expected. The gap between
those two sentences is where this kind of defect lives.

**An agent will find what you ask it to look for.** Ask for "problems" and you
get style notes. Ask pass 1 for correctness *against a named specification* and
you get something worth having.

> When you are done here, run the same five passes on **your own** code. That is
> the real exercise; this was the calibration.

---

*Aldermere Bank is fictional · This file is a teaching artefact, not part of the product*
