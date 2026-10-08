# Features — what to build, and in what order

The [PRD](PRD.md) says what must be true. This says **what to build first**, because you
have 150 minutes and you will not finish everything.

> ### Read this before you plan
>
> **F1 to F8 are the product, and they are one increment.** You build all eight, and
> they reach `table-N` through a single pull request at stage 05. Deploy is the last
> thing that happens, not the middle.
>
> **Build in order. F6, F7 and F8 are cuttable.** If time runs short you drop them,
> and what you ship is a smaller product that is whole rather than a larger one with
> holes in it. **Cut scope, never a stage** — the six stages are what is being
> assessed, and no feature is worth one.

---

## The critical path

```
F1 ingest ──▶ F2 retrieve ──▶ F3 refuse ──▶ F4 generate ──▶ F5 ask + UI
                                                                  │
                                 ┌────────────────────────────────┘
                                 ▼
          F6 follow-up ──▶ F7 corpus browser ──▶ F8 history   all three cuttable
                                 │                            cut from the back
                                 ▼
                      ONE PULL REQUEST ──▶ approved ──▶ merged ──▶ DEPLOY
                                 │
                                 ▼
                      F9 …  F10 …  only after you have shipped
```

**The pull request carries whatever you built**, F1–F8 or F1–F5. What it never carries
is an interface offering more than it has.

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
renders all three outcomes — with the top bar from the UI target.

| | |
|---|---|
| **Covers** | REQ-A1, REQ-A2, REQ-A5, REQ-C1, REQ-C2, REQ-U1, REQ-U1b, REQ-U2 … REQ-U7, REQ-U9 … REQ-U11 |
| **Decisions** | **D7** — citation grouping |
| **Done when** | You can ask in a browser and see a cited answer — **and a refusal looks different from an error** |

> **Nothing deploys here.** F5 is the point at which it becomes a product, not the point
> at which it ships. Keep going; everything goes out together at stage 05.
>
> ⚠️ **The top bar carries only the routes that exist (REQ-U9).** At F5 that is
> **Reset**. **Corpus** arrives with F7, **History** with F8 — add each action when its
> route lands, and never before. A button that goes nowhere is the first thing anyone
> you demo this to will press.

---

# F6 — Follow-up questions

**Should have, and the first of the three you may cut.** It is what makes it a
conversation rather than a search box.

Pass the recent turns to the model so *"and what about above £500?"* means something.

| | |
|---|---|
| **Covers** | REQ-C3 … REQ-C7, REQ-A3, REQ-U8 |
| **Decisions** | **D8** — how many turns · **D9** — whether a follow-up re-retrieves |
| **Done when** | A follow-up is answered correctly, and **Reset** starts clean |
| **If you cut it** | Every question stands alone and **Reset** is the only bar action. Nothing in the interface has to change — say in the release plan that follow-up is not in this release |

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

**Should have, and cuttable.** It is what lets someone check a citation rather than
trust it.

`/corpus` lists the five documents; `/corpus/[id]` shows one, with its sections.

| | |
|---|---|
| **Covers** | REQ-B1 … REQ-B6, REQ-A4, REQ-U12, REQ-U15 |
| **Done when** | **Clicking a citation** opens the document at the section it named, and you can read it |
| **If you cut it** | **No Corpus action in the top bar**, and a citation stays text rather than becoming a link. Citations still name document, section and version — they just cannot be opened |

> Read from `backend/corpus/` (REQ-B5). Copying the documents into the database gives you
> two sources of truth and a bug waiting to happen.
>
> ⚠️ **Render the Markdown (REQ-U12).** The policy tables carry the numbers — thresholds,
> caps, retention periods. Printed as raw `|` and `---` they are unreadable, and a reader
> who cannot read the section cannot check the citation, which is the only reason this
> screen exists.

---

# F8 — History

**Should have, and cuttable.** Every exchange is already stored with its model, prompt version and the
policy versions that answered it. Storing that and never showing it means the only person
who can check what the assistant said is someone with database access.

`/history` lists past conversations, newest first. Opening one shows its turns and lets
you carry on from where it stopped.

| | |
|---|---|
| **Covers** | REQ-C8, REQ-C9, REQ-A6, REQ-U13, REQ-U14 |
| **Done when** | You can leave a conversation, come back to it from `/history`, and ask a follow-up that still has its context |
| **If you cut it** | **No History action in the top bar.** Conversations are still persisted — REQ-C1 and REQ-C2 are F5's, not F8's — so nothing is lost, it is only unread |

> The title is the first question, truncated. Do not add a title column — a second
> source of truth that has to be kept in step with the conversation, for no gain.

---

# Beyond the critical path

**Only after F1–F8 is merged and your URL answers.** Each is genuinely useful and
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

## When you are running out of time

**Cut from the back. F8, then F7, then F6.** Decide it out loud, write it in the ticket
as out of scope, and take the action out of the top bar with the feature. Then carry on
to stage 04 with the time you just bought.

**What you may never cut is a stage.** Review, release and verify are what the module
assesses; the features are what the module uses to assess them. A table that ships F1–F5
through all six stages has done the exercise. A table that reaches F8 by skipping the
review has not done it at all, and the gap is not recoverable afterwards.

> **This is why the eight are a target and not a definition of done.** PRD §12 is the
> authority: done is a completed pipeline and a deployed increment. Building the whole
> product is how you aim; it is not how you are marked.

---

*Policy Assistant · Feature list v2.0 · Build F1–F8, one pull request, then deploy · CONFIDENTIAL — Chartered Vectorial*
