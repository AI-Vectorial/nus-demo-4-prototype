# Stage 04 — Review

**~25 minutes. Five passes, one decision per finding.**

The review is not a formality before merging. **It is the stage most likely to find
something real** — and a finding you accept on purpose is a fine outcome. A finding you
never looked for is not.

---

## Inputs

The diff on `work/table-N` · **`tickets/T0-alignment.md`** · `tickets/T1-plan.md`

## Output

`tickets/T1-review.md`, from `pipeline/templates/review-record.md`.

## The gate

> **Every finding has a decision: fixed, accepted, or deferred — with a reason.**
> A finding with no decision is an open defect.

---

# The prompt

> **Run it with four words.** Tell your agent:
>
> ```
> Follow the prompt in pipeline/04-review.md
> ```
>
> It reads the block below itself. Pasting it also works — but a paste that loses a
> line is a long way to debug, and an edited prompt reaches every table for free.

```
Review the diff on this branch in five separate passes. Keep them
separate -- print each pass under its own heading, do not merge them
into one list -- and go straight on to the next pass without waiting
for me.

  Pass 1  CORRECTNESS      does it do what the ticket says? edge cases?
                           off-by-one? what happens on empty, null, huge?
  Pass 2  SECURITY & PRIVACY   secrets in logs or responses? injection?
                           what happens to the user's question text?
  Pass 3  MAINTAINABILITY  would someone else understand this next month?
                           duplication? swallowed errors? dead code?
  Pass 4  PROVENANCE & IP  every dependency: where from, what licence?
                           anything copied from elsewhere?
  Pass 5  PRODUCTION FITNESS  what happens when Qdrant is down? when the
                           model times out? is failure observable?

For each finding: what it is, where, how bad, and what you would do.
Do NOT fix anything yet. I decide what gets fixed.

Number findings FND-1, FND-2 and so on. Never F1, F2 -- F1 to F12 are
the FEATURES in docs/features.md, so "F11" in a review reads as "Audit
export" and nobody can follow you.

Check before you assert. Do not say "all dependencies are permissive"
unless you have read them; say "I have not checked every transitive
dependency" instead. If you do turn out to be wrong, correct it in one
line and move on -- do not write a paragraph revising your earlier
self. We are reading this for findings, not for your reasoning about
your reasoning.

When you are done, commit what this stage produced to work/table-N:

  git add tickets/
  git commit -m "04 review: five passes, a decision on each finding"

Commit at the end of every stage. A Codespace that dies at 1:30 with
four stages of uncommitted work costs the session; the same crash with
four commits behind it costs nothing.
```

**The agent reviews. The team decides.** An agent that finds and silently fixes has
removed the decision — and the decision is what is being assessed.

---

## Warm up first — ten minutes

**Before you review your own code**, run the five passes on somebody else's:
`docs/review-example/README.md`.

It is short, it is not yours, and **it contains real defects**. Its tests pass.

Reviewing your own work is hard because you already believe it works — you just
watched it work. Ten minutes on a controlled example tells you what finding
something actually feels like, before you turn the method on code you are
attached to.

---

## The five passes

| | Looks for |
|---|---|
| **1 Correctness** | Does it do what was asked? Boundaries, empties, the off-by-one |
| **2 Security & privacy** | Secrets, injection, and **what happens to the question text** — it may contain personal data, and the brief leaves that unresolved |
| **3 Maintainability** | Would a stranger understand this? Swallowed errors, duplication |
| **4 Provenance & IP** | Every dependency's origin and licence. **Copyleft fails the build** |
| **5 Production fitness** | Dependency down, model timing out, failure visible or silent |

> **Pass 4 is not paperwork.** On this project it already caught something real:
> `psycopg` is LGPLv3 and arrived as a side effect of adding Postgres support. Nobody was
> looking for it. That is exactly why the pass exists.

## Recording a finding

```markdown
### F3 — Question text is written to the log at INFO
**Pass:** 2 — security and privacy
**Severity:** medium
**Where:** app/api/ask.py:41
**Decision:** FIXED — removed. A policy question can contain a client
name, and the brief's open question Q3 has not been answered.
```

**Accepting is allowed. Accepting silently is not.**

```markdown
**Decision:** ACCEPTED — the threshold is tuned on thirteen questions and
may not generalise. Recorded as a known limitation; doing better needs a
larger evaluation set, which we do not have today.
```

## Before you leave this stage

- [ ] All five passes were run **separately** and shown separately
- [ ] Every finding has a decision and a reason
- [ ] Everything marked FIXED is actually fixed, and the tests still pass
- [ ] Every dependency's licence is recorded
- [ ] The team can name **one finding they accepted, and why**
