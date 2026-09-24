# Product Requirements — Policy Assistant

**The engineering contract.** The project brief says *why* this product exists. This
document says *what* must be true of it.

| | |
|---|---|
| **Product** | Policy Assistant, for the fictional **Aldermere Bank** |
| **Brief** | [`project-brief.md`](project-brief.md) |
| **Features** | [`features.md`](features.md) |
| **Version** | 1.0 |

> ### How to read this
>
> **§3–§7 are fixed.** The API shape, the data model and the vector payload are
> contracts. Five teams build against them so five results are comparable, and so the
> checks in `ci/` can test anything.
>
> **§9 is yours.** Every decision in it is deliberately unresolved. You will be asked to
> defend your answers at the plan gate. *"The agent chose it"* is not an answer.

---

# 1. What you are building

A staff member types a policy question in plain language. The assistant finds the
relevant passages in Aldermere's policy corpus, composes an answer **from those passages
and nothing else**, and shows which sections it used.

When the corpus cannot support an answer, **it says so and stops.**

```
question ──▶ embed ──▶ search Qdrant ──▶ enough?
                                           │
                            ┌──────────────┴──────────────┐
                            │ no                          │ yes
                            ▼                             ▼
                        REFUSE                    compose answer
                     (no model call)              from passages
                            │                             │
                            └──────────┬──────────────────┘
                                       ▼
                             record it in Postgres
                                       ▼
                                   respond
```

---

# 2. The user and the outcome

Operations and front-office staff who hit a policy question mid-task. **The policy
question is never the job** — it is an obstacle in front of the job.

**Success:** the answer in under a minute, with its source visible, and no need to ask a
colleague.

**The failure that matters most:** a confident answer the corpus does not support. A
refusal is a good outcome. An invention is not.

---

# 3. Functional requirements

Each has an id. Your acceptance criteria should reference them.

## Ingestion

| | |
|---|---|
| **REQ-I1** | A command indexes the whole corpus from empty: `python -m app.ingest` |
| **REQ-I2** | Documents are split on **section boundaries**, never mid-sentence |
| **REQ-I3** | Every passage carries its document id, title, section, version and status |
| **REQ-I4** | Re-running ingestion changes nothing — **same passage count, same ids** |
| **REQ-I5** | `--force` recreates the collection and re-embeds everything |
| **REQ-I6** | Embedding calls are **batched**; a 200-passage corpus is not 200 requests |
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
> less useful, still honest, still working. Build it now; retrofitting it means every
> caller already assumes an answer exists.

## Persistence

| | |
|---|---|
| **REQ-P1** | Every exchange is recorded — **including refusals and degraded answers** |
| **REQ-P2** | Citations are stored with document id, title, section, version and score |
| **REQ-P3** | A persistence failure must not lose the user's answer |

## The endpoint

| | |
|---|---|
| **REQ-A1** | `POST /ask` accepts a question and returns one of three outcomes |
| **REQ-A2** | Every response validates against §4 |
| **REQ-A3** | Every response carries an `exchange_id` that resolves in Postgres |
| **REQ-A4** | `/healthz` reports database, vector store and model reachability |

## The interface

| | |
|---|---|
| **REQ-U1** | A question can be typed and submitted |
| **REQ-U2** | The answer renders with its citations **visible without further interaction** |
| **REQ-U3** | Each citation shows document, section, version and status |
| **REQ-U4** | A **superseded** citation is visibly distinguished |
| **REQ-U5** | A refusal renders differently from an answer **and** differently from an error |
| **REQ-U6** | Degraded mode is visibly degraded — never passages shown as if they were an answer |
| **REQ-U7** | A pending state shows while waiting |
| **REQ-U8** | It works at phone width |

> **REQ-U2 is a product decision, not a layout one.** The brief's assumption A3 is that
> *showing the source is what makes the answer trustworthy*. Hiding citations behind a
> tab tests a different assumption.

---

# 4. The API contract — fixed

## Request

```http
POST /ask
Content-Type: application/json

{ "question": "What is the approval threshold for a travel expense claim?" }
```

## Response — one shape, three outcomes

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
  "exchange_id": "5f2c...",
  "latency_ms": 1840
}
```

| outcome | `answer` | `citations` | when |
|---|---|---|---|
| `answered` | the composed text | the passages used | retrieval was sufficient |
| `refused` | **the reason, and where to go instead** | `[]` | retrieval found nothing above threshold |
| `degraded` | `null` | the passages found | the model was off or unreachable |

> **`outcome` is explicit, never inferred.** A client must not have to deduce a refusal
> from a null answer.

---

# 5. The data model — fixed

```sql
exchanges
  id              uuid primary key
  question        text        not null
  outcome         text        not null   -- answered | refused | degraded
  answer          text        null       -- null for refused and degraded
  model           text        null
  prompt_version  text        null
  latency_ms      integer     not null
  degraded        boolean     not null default false
  created_at      timestamptz not null default now()

exchange_citations
  id              uuid primary key
  exchange_id     uuid        not null references exchanges(id)
  document_id     text        not null
  document_title  text        not null
  section         text        not null
  version         text        not null
  status          text        not null
  score           double precision not null
```

---

# 6. The vector payload — fixed

Every passage stored in Qdrant carries exactly this payload:

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

**This is a contract.** The citation in §4 is built from it, and the shared types in
`app/retrieve/store.py` already express it. Add fields if you need them; do not rename
these.

---

# 7. Configuration — fixed names

Everything arrives from the environment. **No model name, URL, dimension or threshold
appears as a literal in code.**

```bash
OPENROUTER_API_KEY=            OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=openai/gpt-oss-120b  LLM_TIMEOUT_SECONDS=60
EMBEDDING_MODEL=openai/text-embedding-3-small
EMBEDDING_DIM=1536             EMBEDDING_BATCH_SIZE=96

DATABASE_URL=                  DATABASE_NAME=table_N
QDRANT_URL=                    QDRANT_API_KEY=
QDRANT_COLLECTION=policy_passages_table_N

MIN_SCORE=                     # yours to choose -- see §9
CHUNK_MAX_TOKENS=              # yours
CHUNK_OVERLAP_TOKENS=          # yours
GENERATION_ENABLED=true
```

> `DATABASE_NAME` and `QDRANT_COLLECTION` are **set for you** and differ per table. They
> are what keep your data separate from the other four. Do not change them.

---

# 8. Non-functional requirements

| | Target | Why |
|---|---|---|
| **NFR-1** Answer latency | under 5s at p50 | The brief promises under a minute end to end |
| **NFR-2** Refusal latency | under 1.5s | A refusal makes **no model call** — it should be visibly faster |
| **NFR-3** Degradation | the product still serves | The kill switch, REQ-G6 |
| **NFR-4** Ingestion | full corpus under 60s | You will run it more than once |
| **NFR-5** Startup | `/healthz` answers even when Postgres or Qdrant is down | A health check that dies with its dependencies reports nothing |
| **NFR-6** Secrets | never logged, never in a response, never committed | |

> **NFR-2 is a design consequence worth noticing.** If your refusal is slow, you are
> calling the model before deciding whether to answer — which means the model is
> deciding whether it knows something. The brief says it must not.

---

# 9. ⭐ The decisions that are yours

**Deliberately unresolved.** Your implementation plan must state each one and why. You
will be asked at the gate — and *"the agent picked it"* is not an answer.

| # | Decision | What hangs on it |
|---|---|---|
| **D1** | **Chunk size, and whether chunks overlap** | Too large and citations are vague; too small and passages lose the clause that gives them meaning |
| **D2** | **The refusal threshold** — and **how you arrived at it** | Too low and it invents; too high and it refuses what it knows. Tune it against `EVALUATION.md`; do not guess |
| **D3** | **How many passages to retrieve** | More context, or more noise |
| **D4** | **Whether superseded policies are shown, hidden or flagged** | The corpus contains one. Whatever you choose, be able to say why |
| **D5** | **What a refusal says** | *"I don't know"* is not enough. The user needs to know where to go |
| **D6** | **What happens when two policies conflict** | The corpus contains a genuine conflict. Surface both, pick one, or refuse — this is a governance decision, not a coding one |
| **D7** | **How citations are grouped** | Three passages from one document — one citation or three? |
| **D8** | **Where the record is written** | Before responding, or after? What if it fails? |

> **D6 is the one worth arguing about.** Conflicting policy is a problem Aldermere
> already has. Resolving it in code means your software decides which policy wins. That
> may be the wrong call — and saying so is a better answer than a clever implementation.

---

# 10. Out of scope

| | Why |
|---|---|
| Authentication, users, sessions | Not what this teaches |
| Editing policy | The assistant reads; the Policy Office writes |
| Deciding whether an exception is permitted | Judgement stays with humans, by design |
| Anything outside the corpus — no web search, no general knowledge | REQ-G2 |
| Conversation memory / follow-up questions | One question, one answer |
| Re-indexing on document change | Ingestion is a command you run |

---

# 11. Definition of done

> **You are done when you have completed all six stages and deployed a working increment
> to your own URL. Not when the chatbot is feature-complete.**

A team that ships ingestion and retrieval but runs out of time before generation has
still shaped a ticket, defended a plan to a human, built against their own acceptance
criteria, reviewed in five passes, written a rollback, and released through a gate.
**That is the module.**

A polished chatbot with no review record is the worse outcome.

### The evidence

| | |
|---|---|
| 1 | Your ticket, with acceptance criteria **in your words** |
| 2 | Your implementation plan, including **§9's decisions and your reasons** |
| 3 | The plan-gate decision — approved, or rejected and revised |
| 4 | Working code, deployed |
| 5 | Test evidence — something that was red and is now green |
| 6 | A five-pass review record, **with a decision per finding** |
| 7 | A dependency and provenance record |
| 8 | A release plan with a **rollback** |
| 9 | Your live URL, answering |
| 10 | The debrief: where AI helped, where it displaced or risked, **and the control that caught it** |

---

*Policy Assistant · PRD v1.0 · Aldermere Bank is fictional · CONFIDENTIAL — Chartered Vectorial*
