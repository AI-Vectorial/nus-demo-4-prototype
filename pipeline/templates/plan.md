# T1 — Implementation plan

**Stage:** 02 plan
**Ticket:** tickets/T1-<name>.md
**Status:** AWAITING APPROVAL

---

## The decisions

*All ten, from `docs/PRD.md` **§10**. Every row needs a reason beside it — the
reason is what gets asked for at the gate, not the value.*

> **If you took the agent's recommendation, say so and write its reason down.**
> *"Accepted the recommendation: 400 keeps a policy clause whole in one chunk"* is a
> complete answer and an honest one. What fails at the gate is a blank cell, or a value
> with nobody willing to stand behind it — not the fact that the agent suggested it first.

| # | Decision | What we chose | **Why** |
|---|---|---|---|
| D0 | Embedding model and dimensions | | |
| D1 | Chunk size, and whether chunks overlap | | |
| D2 | The refusal threshold — and how we arrived at it | | |
| D3 | How many passages to retrieve | | |
| D4 | Whether superseded policies are shown, hidden or flagged | | |
| D5 | What a refusal says | | |
| D6 | What happens when two policies conflict | | |
| D7 | How citations are grouped | | |
| D8 | How much conversation a follow-up sees | | |
| D9 | Whether a follow-up re-retrieves, and on what text | | |

> ⚠️ **D0 and D2 are coupled**, and **D9 is REQ-C5.** Change D0 or D1 and the threshold
> in D2 is stale — the product refuses everything while every test stays green. Skip
> retrieval on a follow-up and you answer confidently from the *previous* question's
> passages, which looks right and is not.

## What we will build

| Order | File | New / Change | What it does |
|---|---|---|---|
| 1 | | | |

## Why this order

<One or two sentences.>

## What we will NOT do

- <explicitly out of scope for this pass>

## The riskiest part

**Risk:** <what might not work>
**If it fails:** <what we do instead>

---

## Approval

*A role, not a name. Nobody signs anything today — do not ask who approved it.*

| | |
|---|---|
| **Decision** | APPROVED / REJECTED |
| **By** | the release manager |
| **When** | <date, time> |
| **If rejected, what would make it acceptable** | |
