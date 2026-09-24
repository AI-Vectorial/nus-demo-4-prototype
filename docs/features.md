# Features — what to build, and in what order

The [PRD](PRD.md) says what must be true. This says **what to build first**, because you
have 150 minutes and you will not finish everything.

> ### Read this before you plan
>
> **F1 to F5 are the product.** Without all five there is no chatbot.
> **F6 onward are real features** you should reach for only once F1–F5 are deployed.
>
> **Build in order. Deploy as soon as F5 works.** A deployed increment beats an
> undeployed improvement, every time — and the pipeline only completes if something ships.

---

## The critical path

```
F1 ingest ──▶ F2 retrieve ──▶ F3 refuse ──▶ F4 generate ──▶ F5 ask + UI ──▶ DEPLOY
                                                                              │
                        ┌─────────────────────────────────────────────────────┘
                        ▼
              F6 …  F7 …  F8 …        only after you have shipped
```

---

# F1 — Ingest the corpus

**Must have.** Nothing works until the corpus is searchable.

Read `backend/corpus/`, split each document on its section boundaries, embed each
passage, write them to Qdrant with the payload in PRD §6.

| | |
|---|---|
| **Covers** | REQ-I1 … REQ-I7 |
| **Decisions** | **D1** — chunk size and overlap |
| **Done when** | `python -m app.ingest` indexes the corpus, and running it twice changes nothing |

> Idempotency (REQ-I4) is the part most likely to be quietly wrong. Test it by running
> twice and asserting the count did not move. A stable passage id — a hash of document,
> section and text — makes it fall out naturally.

---

# F2 — Retrieve

**Must have.**

Embed the question, search the collection, return the closest passages with their
scores and payload.

| | |
|---|---|
| **Covers** | REQ-R1, REQ-R5 |
| **Decisions** | **D3** — how many passages |
| **Done when** | The ten answerable questions in `corpus/EVALUATION.md` each return their expected section in the top three |

---

# F3 — Refuse

**Must have, and it is the feature this product is judged on.**

Discard passages below the threshold. If nothing survives, **return a refusal and do not
call the model.**

| | |
|---|---|
| **Covers** | REQ-R2, REQ-R3, REQ-R4, REQ-R6 |
| **Decisions** | **D2** — the threshold and how you chose it · **D5** — what the refusal says |
| **Done when** | All three out-of-scope questions refuse, and all ten answerable ones do not |

> **Make refusal a type, not an empty list.** If `retrieve()` returns
> `Grounded | Insufficient`, generation *cannot* run on a refusal — the code will not
> type-check. If it returns `list[Hit]`, someone will eventually call the model with an
> empty list and get a confident invention.
>
> This is a five-line decision that determines whether the product's defining behaviour
> is guaranteed or merely intended.

---

# F4 — Generate

**Must have.**

Compose an answer from the retrieved passages and nothing else. Keep the prompt in a
versioned file.

| | |
|---|---|
| **Covers** | REQ-G1 … REQ-G6 |
| **Decisions** | **D4** — superseded policies · **D6** — conflicting policies |
| **Done when** | An answer cites only retrieved passages, **and `GENERATION_ENABLED=false` still returns something useful** |

> **The kill switch (REQ-G6) is part of F4, not a later polish.** Build it while you are
> writing the call. Once every caller assumes an answer exists, adding degraded mode
> means changing all of them.

---

# F5 — Ask, and show it

**Must have. This is the one that makes it a product.**

`POST /ask` tying F1–F4 together, the record written to Postgres, and an interface that
renders all three outcomes.

| | |
|---|---|
| **Covers** | REQ-A1 … REQ-A4, REQ-P1 … REQ-P3, REQ-U1 … REQ-U8 |
| **Decisions** | **D7** — citation grouping · **D8** — when the record is written |
| **Done when** | You can ask a question in a browser and see a cited answer — **and a refusal looks different from an error** |

> **Deploy here.** Do not wait for F6. The pipeline completes on a deployed increment;
> an undeployed improvement completes nothing.

---

# Beyond the critical path

**Only after F5 is deployed and your URL answers.** Each is genuinely useful and
genuinely optional. Pick whichever your table finds most interesting — you are not
expected to reach these.

### F6 — Conversation history
Past exchanges, retrievable and displayed. The data is already in Postgres from F5.
*Covers: a read path over `exchanges`.*

### F7 — A personal-data guardrail
Flag a question that appears to contain personal or client data before it reaches the
model. **Decide what "personal data" means and write it down** — that definition is the
feature, the regex is not.
*The brief's open question Q3 is unresolved here. You are deciding it.*

### F8 — Was this helpful
Capture a judgement against an `exchange_id`. Success measure S4 in the brief depends on
this existing.

### F9 — Audit export
Download a complete record of an exchange — question, answer, every citation with its
policy version, model, prompt version, timestamp. **This is what makes the product
defensible to an auditor**, and the data model already supports it.

### F10 — Answer confidence
Show how well-grounded an answer is. Harder than it looks: retrieval score is not
confidence, and presenting it as such would be a misleading interface. If you build it,
be able to defend what the number means.

---

## What not to build

| | Why |
|---|---|
| Authentication | Not what this teaches |
| Streaming responses | Nice, not needed, and it complicates every downstream piece |
| Re-ranking, hybrid search, query expansion | Reach for these only if retrieval is measurably failing — and measure first |
| A settings screen | Configuration is environment variables |
| Editing the corpus | **Protected. If retrieval is weak, fix retrieval** |

> **That last line is the trap.** When retrieval underperforms, editing a policy document
> to contain the words you searched for makes the demo work and the product worthless.
> `ci/check_scope.py` will refuse the change — but you should not want to make it.

---

*Policy Assistant · Feature list v1.0 · Build F1–F5, deploy, then choose · CONFIDENTIAL — Chartered Vectorial*
