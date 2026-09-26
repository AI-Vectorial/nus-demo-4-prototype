# Product Requirements — Policy Assistant

**The engineering contract.** The project brief says *why* this product exists. This
document says *what* must be true of it.

| | |
|---|---|
| **Product** | Policy Assistant, for the fictional **Aldermere Bank** |
| **Stack** | **FastAPI** (Python 3.12) · **React** via Next.js · Postgres · Qdrant · OpenRouter |
| **Brief** | [`project-brief.md`](project-brief.md) |
| **Features** | [`features.md`](features.md) |
| **UI target** | the screens you were shown — build to them |
| **Version** | 2.0 |

> ### How to read this
>
> **§4–§8 are fixed.** The routes, the data model and the vector payload are contracts.
> Five tables build against them so five results are comparable, and so the checks in
> `ci/` can test anything.
>
> **§10 is yours.** Every decision in it is deliberately unresolved. You will be asked to
> defend your answers at the plan gate. *"The agent chose it"* is not an answer.

---

# 1. What you are building

A staff member opens the assistant and asks a policy question in plain language. The
assistant finds the relevant passages in Aldermere's policy corpus, composes an answer
**from those passages and nothing else**, and shows which sections it used.

They can **ask a follow-up**, and it understands what "it" refers to.

When the corpus cannot support an answer, **it says so and stops.**

They can also **browse the corpus** — see the five policy documents and read any section
the assistant cited.

```
question ──▶ embed ──▶ search Qdrant ──▶ enough?
   ▲                                       │
   │                        ┌──────────────┴──────────────┐
   │                        │ no                          │ yes
   │                        ▼                             ▼
   │                    REFUSE                    compose answer
   │                 (no model call)              from passages
   │                        │                     + recent turns
   │                        └──────────┬──────────────────┘
   │                                   ▼
   └──── follow-up ────── save the turn to the conversation
                                       ▼
                                    respond
```

---

# 2. The screens

Four routes. **No settings page.**

| Route | What it is |
|---|---|
| **`/`** | The assistant. Empty state → ask → answer → follow-up |
| **`/history`** | Past conversations, newest first. Open one to read it |
| **`/corpus`** | The five documents, each with owner, version, effective date and status |
| **`/corpus/[id]`** | One document, with its sections down the left and the text beside them |

**A top bar runs across every route.** The product name on the left; on the right three
actions — **Reset** (start a fresh conversation), **History**, **Corpus**. No sidebar, no
collapsing rail, no hamburger.

> **Why history is a screen and not just a table.** Every exchange is already stored with
> the model, the prompt version and the policy versions that answered it — REQ-P1, and the
> thing that makes the product defensible to an auditor. Storing that and never showing it
> means the only person who can check what the assistant said is someone with database
> access.

> **Why no conversation list.** One conversation at a time is enough to demonstrate
> follow-up, and a history browser is a feature you would build after shipping, not
> before. **Conversations are still persisted** — the data is there when it is wanted.

---

# 3. The user and the outcome

Operations and front-office staff who hit a policy question mid-task. **The policy
question is never the job** — it is an obstacle in front of the job.

**Success:** the answer in under a minute, with its source visible, and no need to ask a
colleague.

**The failure that matters most:** a confident answer the corpus does not support. A
refusal is a good outcome. An invention is not.

---

# 4. Functional requirements

Each has an id. Your acceptance criteria should reference them.

## Ingestion

| | |
|---|---|
| **REQ-I1** | A command indexes the whole corpus from empty: `python -m app.ingest` |
| **REQ-I2** | Documents are split on **section boundaries**, never mid-sentence |
| **REQ-I3** | Every passage carries its document id, title, section, version and status |
| **REQ-I4** | Re-running ingestion changes nothing — **same passage count, same ids** |
| **REQ-I5** | `--force` recreates the collection and re-embeds everything |
| **REQ-I6** | Embedding calls are **batched** |
| **REQ-I7** | Superseded documents are indexed **with `status: superseded`**, not excluded |

> **REQ-I7 matters.** *"Is this still current?"* is a real question. Excluding superseded
> policy makes it unanswerable.

## Retrieval

| | |
|---|---|
| **REQ-R1** | A question is embedded and matched against the indexed passages |
| **REQ-R2** | Passages scoring below the threshold are **discarded** |
| **REQ-R3** | Retrieval returns either **grounded passages** or an **explicit insufficiency** — never an ambiguous empty list |
| **REQ-R4** | The threshold is read from configuration, not written in code |
| **REQ-R5** | All ten answerable questions in `corpus/EVALUATION.md` return passages, with the expected section in the top three |
| **REQ-R6** | All three out-of-scope questions return insufficiency |

> **REQ-R3 is the one to get right.** Make refusal a *type*, not an empty list. Then
> generation cannot run on a refusal by accident — the code will not compile that way.
>
> This is not theoretical. Asked *"Can I expense my partner's flight?"* with only
> irrelevant policy in context, `gpt-oss-120b` restated the irrelevant policy rather than
> declining. **A model asked whether it knows something will answer with whatever it
> has.** The rule has to live in code.

## Conversation

| | |
|---|---|
| **REQ-C1** | A conversation is created on the first question and persists |
| **REQ-C2** | Every turn — question and answer — is stored against its conversation |
| **REQ-C3** | A follow-up question is answered **with the recent turns in context** |
| **REQ-C4** | How many turns is configurable (`CONTEXT_MESSAGES`), default **5** |
| **REQ-C5** | **Retrieval still runs on every turn.** Context informs the answer; it never replaces the search |
| **REQ-C6** | **New chat** starts a fresh conversation with no prior context |
| **REQ-C7** | A follow-up is **embedded together with the questions before it**, not on its own |
| **REQ-C8** | Conversations are **listable**, newest first, each with enough to recognise it |
| **REQ-C9** | Opening a past conversation shows its turns **and lets the user continue it** |

> **REQ-C5 is the trap.** It is tempting to skip retrieval on a follow-up because "we
> already have the passages". Do not. *"And what about above £500?"* needs different
> passages from the question before it, and reusing the old ones produces a confident
> answer from the wrong section.
>
> An easy mistake to make and a hard one to notice, because the answer still looks right.
>
> ⚠️ **REQ-C7 is the other half of it, and it bites in the opposite direction.** Run
> retrieval on the follow-up *alone* and *"and what about above £500?"* embeds to
> nothing — no policy vocabulary, no match, refused. The answer was one row further down
> the table the previous question already found.
>
> **Retrieval runs on the conversation; the answer is composed for the question asked.**
> Carry the user turns only — carrying the assistant's answers drags every query back
> toward the passages already found, so a follow-up could never reach a section the
> first answer missed.
>
> *(Both halves were found by deploying the reference build and asking a follow-up.)*

## Generation

| | |
|---|---|
| **REQ-G1** | An answer is composed **only** from retrieved passages |
| **REQ-G2** | The model is never asked to answer from its own knowledge |
| **REQ-G3** | Every answer carries the passages that produced it |
| **REQ-G4** | The prompt lives in a **versioned file**, not a string literal |
| **REQ-G5** | Every answer records its `prompt_version`, `model` and `latency_ms` |
| **REQ-G6** | **The kill switch.** With `GENERATION_ENABLED=false`, or when the provider is unreachable, the product returns the retrieved passages with **no composed answer** and a degraded flag |

> **REQ-G6 is a deliverable, not a nice-to-have.** The brief's §9 states the test: *turn
> the model off and see what is left*. What is left must be a working policy search —
> less useful, still honest, still working. Build it while you write the model call;
> retrofitting it means changing every caller.

## Corpus browsing

| | |
|---|---|
| **REQ-B1** | `/corpus` lists every document with title, owner, version, effective date and status |
| **REQ-B2** | A **superseded** document is visibly distinguished in the list |
| **REQ-B3** | `/corpus/[id]` shows one document's sections and their text |
| **REQ-B4** | The section list is navigable — clicking one moves to it |
| **REQ-B6** | Both corpus routes offer a way **back** — to the list, and to the assistant |
| **REQ-B5** | Documents are read from `backend/corpus/`, not duplicated in the database |

## The API

| | |
|---|---|
| **REQ-A1** | `POST /ask` accepts a question and an optional conversation, and returns one of three outcomes |
| **REQ-A2** | Every response validates against §5 |
| **REQ-A3** | `GET /conversations/{id}` returns a conversation and its turns |
| **REQ-A4** | `GET /corpus` and `GET /corpus/{id}` serve the documents |
| **REQ-A6** | `GET /conversations` lists them, newest first, paginated |
| **REQ-A5** | `/healthz` reports database, vector store and model reachability |

## The interface

| | |
|---|---|
| **REQ-U1** | An empty state invites a question, centred, with a send control |
| **REQ-U2** | Asking shows the question, then the answer, with **citations visible without further interaction** |
| **REQ-U3** | Each citation shows document, section, version and status |
| **REQ-U4** | A **superseded** citation is visibly distinguished |
| **REQ-U5** | A refusal renders differently from an answer **and** differently from an error |
| **REQ-U6** | Degraded mode is visibly degraded — never passages shown as if they were an answer |
| **REQ-U7** | A pending state shows while waiting |
| **REQ-U8** | A follow-up can be asked without losing the conversation above it |
| **REQ-U9** | A **top bar** on every route, with exactly three actions: **Reset**, **History**, **Corpus** |
| **REQ-U10** | It works at phone width |
| **REQ-U11** | **Light theme only.** No dark mode, no theme switch |
| **REQ-U12** | Markdown in a policy section renders as **markup, not as literal characters** — tables as tables |
| **REQ-U13** | `/history` lists past conversations; opening one shows it and allows a follow-up |
| **REQ-U14** | A conversation with no turns is never listed |
| **REQ-U15** | **A citation opens the section it names** in the corpus browser |

> **REQ-U2 is a product decision, not a layout one.** The brief's assumption A3 is that
> *showing the source is what makes the answer trustworthy*. Hiding citations behind a
> tab tests a different assumption.
>
> **REQ-U15 is what makes a citation a source.** One nobody can follow is a claim.
> Link by **heading**, not by anchor: the anchor carries a section's position in its
> document, a citation cannot know it, and the two versions of the travel policy number
> their sections differently — 4.2 in one is 4.1 in the other.
>
> ⚠️ **REQ-U12 is not cosmetic.** The corpus is written in Markdown and its tables carry
> the numbers — the approval thresholds, the accommodation caps, the retention periods.
> Rendered as raw pipes and dashes they are unreadable, so a reader cannot check the
> citation, and checking the citation is the point of the corpus browser.

## The theme

| | |
|---|---|
| Background | `#fafafc` |
| Panel | `#ffffff` |
| Surface tint | `#eef1f3` |
| Border | `#dfe5e8` · strong `#c8d2d6` |
| Text | `#00141a` · dim `#5b6b72` |
| Accent | `#00ad6d` · soft `rgba(0,173,109,0.12)` |
| Danger | `#c0442f` |
| Warning | `#8a6516` on `#fdf6da`, border `#ecd894` |
| Type | **Space Grotesk**, system-ui fallback |

Taken from Module 3 unchanged, so a participant moving between modules sees one product,
not two. **Light only** — REQ-U11.

---

# 5. The API contract — fixed

## Ask

```http
POST /ask
{ "question": "What is the approval threshold?", "conversation_id": null }
```

`conversation_id` is `null` on the first question and the id thereafter.

```jsonc
{
  "outcome": "answered",          // "answered" | "refused" | "degraded"
  "answer": "Claims of £75 or more require line-manager approval before...",
  "citations": [
    {
      "document_id": "travel-expense-policy",
      "document_title": "Travel and Expense Policy",
      "section": "4.2 Approval thresholds",
      "version": "3.1",
      "status": "current",        // "current" | "superseded"
      "score": 0.82
    }
  ],
  "conversation_id": "9c1e...",
  "message_id": "5f2c...",
  "latency_ms": 1840
}
```

| outcome | `answer` | `citations` | when |
|---|---|---|---|
| `answered` | the composed text | the passages used | retrieval was sufficient |
| `refused` | **the reason, and where to go instead** | `[]` | nothing scored above the threshold |
| `degraded` | `null` | the passages found | the model was off or unreachable |

> **`outcome` is explicit, never inferred.** A client must not have to deduce a refusal
> from a null answer.

## Conversation

```http
GET /conversations?limit=50
[ { "id": "9c1e...", "started_at": "...", "last_at": "...",
    "title": "What is the approval threshold...",   // the first question, truncated
    "message_count": 4 } ]

GET /conversations/{id}
{ "id": "9c1e...", "started_at": "...", "messages": [ { "role": "user" | "assistant", ... } ] }
```

`title` is derived from the first user message — there is no separate title to keep in
step with anything.

## Corpus

```http
GET /corpus            → [ { id, title, owner, version, effective, status, sections } ]
GET /corpus/{id}       → { id, title, owner, version, effective, status,
                           sections: [ { heading, text } ] }
```

---

# 6. The data model — fixed

```sql
conversations
  id            uuid primary key
  started_at    timestamptz not null default now()
  last_at       timestamptz not null default now()

messages
  id              uuid primary key
  conversation_id uuid        not null references conversations(id) on delete cascade
  role            text        not null   -- user | assistant
  content         text        null       -- the question, or the answer
  outcome         text        null       -- answered | refused | degraded (assistant only)
  model           text        null
  prompt_version  text        null
  latency_ms      integer     null
  created_at      timestamptz not null default now()

message_citations
  id              uuid primary key
  message_id      uuid        not null references messages(id) on delete cascade
  document_id     text        not null
  document_title  text        not null
  section         text        not null
  version         text        not null
  status          text        not null
  score           double precision not null
```

> **`messages` is both the record and the context.** The last `CONTEXT_MESSAGES` rows of
> a conversation are what a follow-up is answered with — so there is no second store to
> keep in step, and the thing an auditor reads is the same thing the model read.

---

# 7. The vector payload — fixed

```jsonc
{
  "text": "Claims of £75 or more require...",
  "document_id": "travel-expense-policy",
  "document_title": "Travel and Expense Policy",
  "section": "4.2 Approval thresholds",
  "version": "3.1",
  "status": "current",
  "effective": "2026-04-01"
}
```

**This is a contract.** The citation in §5 is built from it, and the shared types in
`app/retrieve/store.py` already express it. Add fields if you need them; do not rename
these.

---

# 8. Configuration — fixed names

Everything arrives from the environment. **No model name, URL, dimension or threshold
appears as a literal in code.**

```bash
OPENROUTER_API_KEY=            OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=openai/gpt-oss-120b  LLM_TIMEOUT_SECONDS=60

EMBEDDING_MODEL_SLUG=openai/text-embedding-3-small
EMBEDDING_DIMENSIONS=1536      EMBEDDING_BATCH_SIZE=96

DATABASE_URL=                  DATABASE_NAME=table_N
QDRANT_URL=                    QDRANT_COLLECTION=policy_passages_table_N

MIN_SCORE=                     # yours -- see §10
CHUNK_MAX_TOKENS=              # yours
CHUNK_OVERLAP_TOKENS=          # yours
RETRIEVE_TOP_K=                # yours
CONTEXT_MESSAGES=5             # yours -- how many turns a follow-up sees
GENERATION_ENABLED=true
```

> `DATABASE_NAME` and `QDRANT_COLLECTION` are **set for you** and differ per table. They
> are what keep your data separate from the other four. Do not change them.

---

# 9. Non-functional requirements

| | Target | Why |
|---|---|---|
| **NFR-1** Answer latency | under 5s at p50 | The brief promises under a minute end to end |
| **NFR-2** Refusal latency | under 1.5s | A refusal makes **no model call** — it should be visibly faster |
| **NFR-3** Degradation | the product still serves | The kill switch, REQ-G6 |
| **NFR-4** Ingestion | full corpus under 60s | You will run it more than once |
| **NFR-5** Startup | `/healthz` answers even when Postgres or Qdrant is down | A health check that dies with its dependencies reports nothing |
| **NFR-6** Secrets | never logged, never in a response, never committed | |

> **NFR-2 is a design consequence worth noticing.** If your refusal is slow, you are
> calling the model before deciding whether to answer — which means the model is deciding
> whether it knows something. The brief says it must not.

---

# 10. ⭐ The decisions that are yours

**Deliberately unresolved.** Your implementation plan must state each one and why. You
will be asked at the gate — and *"the agent picked it"* is not an answer.

| # | Decision | What hangs on it |
|---|---|---|
| **D0** | **Embedding model and dimensions** | 1536 is cheaper, 3072 is better. **The Qdrant collection is fixed at the dimension you first index with** — changing later means re-indexing |
| **D1** | **Chunk size, and whether chunks overlap** | Too large and citations are vague; too small and passages lose the clause that gives them meaning |
| **D2** | **The refusal threshold** — and **how you arrived at it** | Tune it against `EVALUATION.md`; do not guess |
| **D3** | **How many passages to retrieve** | More context, or more noise |
| **D4** | **Whether superseded policies are shown, hidden or flagged** | The corpus contains one. Whatever you choose, be able to say why |
| **D5** | **What a refusal says** | *"I don't know"* is not enough. The user needs to know where to go |
| **D6** | **What happens when two policies conflict** | The corpus contains a genuine conflict. Surface both, pick one, or refuse — a governance decision, not a coding one |
| **D7** | **How citations are grouped** | Three passages from one document — one citation or three? |
| **D8** | **How much conversation a follow-up sees** | Too little and "what about above £500?" is meaningless; too much and old turns drag the answer off course |
| **D9** | **Whether a follow-up re-retrieves, and on what text** | REQ-C5 says it must re-retrieve; REQ-C7 says it must do so on the conversation, not the fragment. Be able to say why both are right |

> **D6 is the one worth arguing about.** Conflicting policy is a problem Aldermere
> already has. Resolving it in code means your software decides which policy wins. That
> may be the wrong call — and saying so is a better answer than a clever implementation.

---

# 11. Out of scope

| | Why |
|---|---|
| **A settings page** | Configuration is environment variables. Do not build a UI for it |
| Authentication, users, sessions | Not what this teaches |
| Editing policy | The assistant reads; the Policy Office writes |
| Deciding whether an exception is permitted | Judgement stays with humans, by design |
| Anything outside the corpus — no web search, no general knowledge | REQ-G2 |
| Re-indexing on document change | Ingestion is a command you run |
| Streaming responses | Nice, not needed, and it complicates everything downstream |

---

# 12. Definition of done

> **You are done when you have completed all six stages and deployed a working increment
> to your own URL. Not when the product is feature-complete.**

A team that ships ingestion and retrieval but runs out of time before generation has
still shaped a ticket, defended a plan to a human, built against their own acceptance
criteria, reviewed in five passes, written a rollback, and released through a gate.
**That is the module.**

A polished product with no review record is the worse outcome.

### The evidence

| | |
|---|---|
| 1 | Your ticket, with acceptance criteria **in your words** |
| 2 | Your implementation plan, including **§10's decisions and your reasons** |
| 3 | The plan-gate decision — approved, or rejected and revised |
| 4 | Working code, deployed |
| 5 | Test evidence — something that was red and is now green |
| 6 | A five-pass review record, **with a decision per finding** |
| 7 | A dependency and provenance record |
| 8 | A release plan with a **rollback** |
| 9 | Your live URL, answering |
| 10 | The debrief: where AI helped, where it displaced or risked, **and the control that caught it** |

---

*Policy Assistant · PRD v2.0 · Aldermere Bank is fictional · CONFIDENTIAL — Chartered Vectorial*
