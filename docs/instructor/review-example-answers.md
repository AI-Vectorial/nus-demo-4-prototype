# Review warm-up — what is actually in it

⚠️ **INSTRUCTOR ONLY.** In the participant repo because it travels with the
code. A table that opens it has only cheated itself.

**File:** `docs/review-example/expense_rules.py`
**Four defects, one per pass, plus a clean pass 4.**

---

## 1 — Correctness ⭐ the one that matters

```python
if claim.amount_gbp > 75:      # policy says "75 pounds OR MORE"
```

**A claim of exactly £75 is auto-approved and nobody ever sees it.**

`travel-expense-policy-v3.1.md` §4.2: *"A claim of exactly £75 requires
line-manager approval. Thresholds are inclusive of the stated value."*

| Amount | Code says | Policy says |
|---|---|---|
| £74.99 | auto | auto ✅ |
| **£75.00** | **auto** | **line manager** ❌ |
| £75.01 | line manager | line manager ✅ |

**Why it survives review if nobody looks:** every test passes. They test £40,
£120, £500 and £3000 — the boundary is never touched. And the very next line
uses `>= 500` correctly, so the file looks internally consistent at a glance.

**If a table misses this, stop and walk the room through it.** It is the single
most important minute of M04.4.

> **The wider point:** an agent wrote this from a prompt saying *"claims of £75
> or more require approval"*. It produced `> 75`. The prose and the code differ
> by one character and nothing automated notices.

## 2 — Security

```python
try:
    store.save(claim.id, status)
except Exception:
    pass
```

A claim reports `auto_approved` **even when nothing was recorded**. Silent data
loss, and an audit trail with holes in it. `AGENTS.md` §6 names this exact
pattern — *"do not catch an exception you are not handling"*.

Some tables will call this correctness rather than security. **Accept it** — the
pass it lands in matters far less than noticing it.

## 3 — Data and privacy

```python
log.info("claim %s from %s (%s) for %.2f needs %s",
         claim.id, claim.claimant_name, claim.claimant_email, ...)
```

**A name and an email address in the application log**, on every claim. Logs go
to Railway, are retained, and are readable by anyone with deploy access.
`claim.id` alone identifies the claim; the rest is personal data nobody needs.

Good follow-up question: *"Where do your logs go, and who can read them?"*

## 4 — Dependencies

**Clean. Nothing imported beyond the standard library.**

⚠️ **Leave this pass empty and let them find nothing.** A table that "finds"
something here is pattern-matching on the exercise rather than reading the
code — worth naming gently if it happens.

## 5 — Maintainability

`75`, `500` and `2500` are **literals**. PRD §8 requires configuration. When the
threshold moves — and it already has once, £50 → £75 — this needs a code change
and a deploy rather than an environment variable.

Strong tables also spot that `submit()` takes an untyped `store`.

---

## Running it

| | |
|---|---|
| **10 minutes** of stage 04's 25 |
| One pass per prompt. All five at once returns a shallow list of five |
| **Do not let them run the tests first.** Green tests anchor everyone to "it works" |

## Grading, roughly

| Found | |
|---|---|
| 1 only | fine — that is the one that matters |
| 1 + 3 | good |
| 1 + 2 + 3 + 5 | excellent, and rare in ten minutes |
| 4 "findings" including pass 4 | they are guessing; slow them down |

## If a table finds nothing

Do not give the answer. Ask:

> *"What does the policy say happens at exactly £75? Now read line 34 again."*

Almost nobody needs a third hint.

---

*M04 · Instructor material · not for participants*
