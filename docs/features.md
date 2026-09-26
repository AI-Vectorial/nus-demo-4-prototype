# Features — what to build, and in what order

The [PRD](PRD.md) says what must be true. This says **what to build first**, because you
have 150 minutes and you will not finish everything.

> ### Read this before you plan
>
> **F1 to F6 are the product.** Without all six there is no assistant.
>
> **Build in order. Deploy as soon as F5 works.** A deployed increment beats an
> undeployed improvement, every time — and the pipeline only completes if something ships.

---

## The critical path

```
F1 ingest ──▶ F2 retrieve ──▶ F3 refuse ──▶ F4 generate ──▶ F5 ask + UI ──▶ DEPLOY
                                                                   │
                                            F6 follow-up ◀─────────┘
                                            F7 corpus browser
                                            F8 history
                                                   │
                                        F9 …  F10 …  only after you have shipped
```

---

# F1 — Ingest the corpus

**Must have.** Nothing works until the corpus is searchable.

Read `backend/corpus/`, split each document on its section boundaries, embed each
passage, write them to Qdrant with the payload in PRD §7.

| | |
|---|---|
| **Covers** | REQ-I1 … REQ-I7 |
| **Decisions** | **D0** — embedding model and dimensions · **D1** — chunk size and overlap |
| **Done when** | `python -m app.ingest` indexes the corpus, and running it twice changes nothing |

> Idempotency (REQ-I4) is the part most likely to be quietly wrong. Test it by running
> twice and asserting the count did not move. A stable passage id — a hash of document,
> section and text — makes it fall out for free.

---

# F2 — Retrieve

**Must have.**

Embed the question, search the collection, return the closest passages with their scores
and payload.

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
> We tested this: asked *"Can I expense my partner's flight?"* with only irrelevant
> policy in context, `gpt-oss-120b` restated the irrelevant policy rather than declining.
> **The model will not save you here.** Five lines of typing will.

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
> writing the call. Once every caller assumes an answer exists, adding degraded mode means
> changing all of them.

---

# F5 — Ask, and show it

**Must have. This is the one that makes it a product.**

`POST /ask` tying F1–F4 together, the turn written to Postgres, and an interface that
renders all three outcomes — with the left rail from the UI target.

| | |
|---|---|
| **Covers** | REQ-A1, REQ-A2, REQ-A5, REQ-C1, REQ-C2, REQ-U1 … REQ-U7, REQ-U9 … REQ-U11 |
| **Decisions** | **D7** — citation grouping |
| **Done when** | You can ask in a browser and see a cited answer — **and a refusal looks different from an error** |

> **Deploy here.** Do not wait for F6. The pipeline completes on a deployed increment; an
> undeployed improvement completes nothing.

---

# F6 — Follow-up questions

**Must have** — it is what makes it a conversation rather than a search box.

Pass the recent turns to the model so *"and what about above £500?"* means something.

| | |
|---|---|
| **Covers** | REQ-C3 … REQ-C7, REQ-A3, REQ-U8 |
| **Decisions** | **D8** — how many turns · **D9** — whether a follow-up re-retrieves |
| **Done when** | A follow-up is answered correctly, and **Reset** starts clean |

> ⚠️ **Retrieval still runs on every turn (REQ-C5).** It is tempting to skip it on a
> follow-up because you already have passages. Do not. *"And what about above £500?"*
> needs a different passage from the question before it, and reusing the old ones gives a
> confident answer from the wrong section.
>
> Easy to get wrong, hard to notice — the answer still looks right.
>
> ⚠️ **And the opposite mistake costs you the feature entirely.** Retrieve on the
> follow-up *alone* and *"and what about above £500?"* matches nothing — it contains no
> policy vocabulary — so it refuses. **Embed the conversation, answer the question.**
> User turns only: the assistant's answers summarise passages already found, and
> carrying them stops a follow-up ever reaching a new section.

---

# F7 — Browse the corpus

**Should have.** It is what lets someone check a citation rather than trust it.

`/corpus` lists the five documents; `/corpus/[id]` shows one, with its sections.

| | |
|---|---|
| **Covers** | REQ-B1 … REQ-B6, REQ-A4, REQ-U12, REQ-U15 |
| **Done when** | **Clicking a citation** opens the document at the section it named, and you can read it |

> Read from `backend/corpus/` (REQ-B5). Copying the documents into the database gives you
> two sources of truth and a bug waiting to happen.
>
> ⚠️ **Render the Markdown (REQ-U12).** The policy tables carry the numbers — thresholds,
> caps, retention periods. Printed as raw `|` and `---` they are unreadable, and a reader
> who cannot read the section cannot check the citation, which is the only reason this
> screen exists.

---

# F8 — History

**Should have.** Every exchange is already stored with its model, prompt version and the
policy versions that answered it. Storing that and never showing it means the only person
who can check what the assistant said is someone with database access.

`/history` lists past conversations, newest first. Opening one shows its turns and lets
you carry on from where it stopped.

| | |
|---|---|
| **Covers** | REQ-C8, REQ-C9, REQ-A6, REQ-U13, REQ-U14 |
| **Done when** | You can leave a conversation, come back to it from `/history`, and ask a follow-up that still has its context |

> The title is the first question, truncated. Do not add a title column — a second
> source of truth that has to be kept in step with the conversation, for no gain.

---

# Beyond the critical path

**Only after F5 is deployed and your URL answers.** Each is genuinely useful and
genuinely optional.

### F9 — Was this helpful
Capture a judgement against a `message_id`. Success measure S4 in the brief depends on it.

### F10 — A personal-data guardrail
Flag a question that appears to contain personal or client data before it reaches the
model. **Decide what "personal data" means and write it down** — that definition is the
feature, the regex is not.

### F11 — Audit export
Download a complete record of a conversation — every question, answer, citation with its
policy version, model, prompt version, timestamp. **This is what makes the product
defensible to an auditor.**

### F12 — Answer confidence
Show how well-grounded an answer is. Harder than it looks: retrieval score is not
confidence, and presenting it as such would be a misleading interface. If you build it,
be able to defend what the number means.

---

## What not to build

| | Why |
|---|---|
| **A settings page** | Configuration is environment variables. Explicitly out of scope |
| Authentication | Not what this teaches |
| Streaming responses | Nice, not needed, complicates every downstream piece |
| Re-ranking, hybrid search, query expansion | Only if retrieval is measurably failing — and measure first |
| Editing the corpus | **Protected. If retrieval is weak, fix retrieval** |

> **That last line is the trap.** When retrieval underperforms, editing a policy document
> to contain the words you searched for makes the demo work and the product worthless.
> `ci/check_scope.py` will refuse the change — but you should not want to make it.

---

*Policy Assistant · Feature list v2.0 · Build F1–F5, deploy, then F6 · CONFIDENTIAL — Chartered Vectorial*
