# tickets

**Your evidence trail. This is what M04 actually assesses.**

The chatbot is the excuse; these files are the work.

---

## The shape

One **epic** for the increment, one **child** per feature — the same way an
epic and its issues sit in Linear.

```
tickets/
  T1.md                  the epic. What we are building, and the acceptance
                         criteria IN YOUR WORDS. Written at stage 01

  T1-F1-ingest.md        one child per feature. Requirement ids, a single
  T1-F2-retrieve.md      pass-or-fail "Done when", and the decisions it
  T1-F3-refuse.md        depends on. Ticked off during stage 03
  T1-F4-generate.md
  T1-F5-ask-and-ui.md

  T1-plan.md             stage 02. The decisions, YOUR reasons, build order
  T1-review.md           stage 04. Five passes, a decision per finding
  T1-release.md          stage 05. How it ships, and how it comes back
```

> **One epic, one plan, one review, one release.** The children track *progress*;
> they do not each run the pipeline. Five passes through six stages does not fit
> 150 minutes, and would not teach anything the first pass did not.

---

## Why it is split this way

**The epic carries the acceptance criteria**, because that is the thing you have
to write in your own words and defend. It is one conversation, not five.

**The children carry the tracking.** F3 is either done or it is not, and anyone
walking past can see which. That is what a board gives you, without a board.

**The plan, the review and the release belong to the increment**, not to a
feature. You do not write five rollbacks for one deploy.

---

## Keeping them honest during the build

At the end of each feature, before moving on:

```
Update tickets/T1-F<n>-*.md: set Status to done, and paste the command
output that shows the "Done when" line is satisfied.
```

**A child marked done with nothing behind it is worse than one left open** — it
turns the trail into a claim.

---

## How these get reviewed

**In the pull request, next to the code.** All of them appear in *Files changed*
at stage 05, so the reviewer sees what you said you would build, the plan that
was approved, what review found, and the rollback — in one diff, beside the
implementation.

**That is deliberate.** The record and the code are approved together, so nobody
can write the review afterwards to match what shipped.

---

*Aldermere Bank is fictional*
