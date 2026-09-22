# Project Brief — Policy Assistant

| | |
|---|---|
| **Product** | Policy Assistant |
| **Organisation** | **Aldermere Bank** — a fictional institution. Every name, policy, figure and document in this project is invented |
| **Sponsor** | Chief Operating Officer |
| **Author** | Operations Change, on behalf of the COO |
| **Status** | Approved for build |
| **Version** | 1.0 |

> **A note on the figures in this document.** Every number here is **supplied case
> data**, not a measurement. They exist so the product has something concrete to be
> judged against. They are fictional and must not be presented as evidence of
> anything.

---

# 1. The concept, in one line

> **A tool that answers a staff member's policy question in seconds, in plain
> language, and shows exactly which policy section the answer came from.**

---

# 2. Who this is for

**Operations and front-office staff at Aldermere Bank** — roughly 1,400 people who
hit a policy question in the middle of doing something else.

A settlements analyst part-way through a break investigation. A relationship manager
with a client on the phone asking whether a fee can be waived. An onboarding officer
unsure whether a document set is complete.

They share one thing: **the policy question is never the job.** It is an obstacle in
front of the job, and every minute spent on it is a minute not spent on the work.

**Not built for** compliance and risk officers, who need the source documents
themselves rather than an answer. They are beneficiaries — fewer interruptions — not
users.

---

# 3. The problem today

There is no single place to find out what Aldermere's policy actually is.

**Policy lives in at least four places, and none of them is definitive:**

| Where | What's wrong with it |
|---|---|
| The policy intranet | Authoritative, but search returns document titles rather than answers. Finding the clause means opening a 40-page PDF and using Ctrl-F |
| A shared drive | Working copies, superseded drafts and current versions sitting in the same folders, distinguishable only by filename convention that not everyone follows |
| Email from Compliance | Accurate at the time it was sent. Forwarded onwards for years afterwards, long after the policy changed |
| Colleagues | Fast, usually right, occasionally confidently wrong, and completely unrecorded |

**The compounding problem is not that the answer is hard to find. It is that a
member of staff cannot tell which of the four answers they just got is the current
one.** So they either ask again through a slower and more trustworthy channel, or
they act on the fastest answer and hope.

### Supplied baseline *(fictional case data)*

| | |
|---|---|
| Median time to resolve a routine policy question | **18 minutes** |
| Proportion answered by interrupting a colleague | **61%** |
| Policy questions reaching the Compliance mailbox each month | **~400** |
| Median Compliance response time | **1.5 working days** |
| Of a sample of 50 answered questions, answers citing a superseded policy version | **9** |

**That last row is the one that matters.** The cost of the current state is not
slowness. It is that roughly one answer in six is quietly wrong, and nobody finds out
until an audit does.

---

# 4. The outcome we want

**For the staff member:** ask the question in their own words, get an answer in under
a minute, and be able to see the policy section it came from without leaving the page.

**For the bank:** policy answers become consistent, traceable and current — and when
a policy changes, every answer changes with it, because the answer is derived from the
document rather than remembered from an email.

**What this is not.** It is not a replacement for Compliance, and it does not make
decisions. It answers *"what does the policy say?"* It never answers *"what should I
do?"* An exception, a judgement call or an edge case still goes to a human, and the
product should make that boundary obvious rather than blur it.

---

# 5. Value hypothesis and success measures

**The hypothesis:**

> If staff can get a cited, current policy answer in under a minute, they will stop
> asking colleagues and stop acting on stale email — and the number of answers based
> on superseded policy will fall sharply.

**How we will know**, measured 30 days after release:

| # | Measure | Baseline | Target | How it is observed |
|---|---|---|---|---|
| **S1** | Median time to a usable policy answer | 18 min | **< 2 min** | Session timing, question asked to answer displayed |
| **S2** | Share of answers carrying a citation to a current policy version | — | **> 95%** | Every answer records the document versions it used |
| **S3** | Questions reaching the Compliance mailbox | ~400/month | **< 250/month** | Mailbox volume |
| **S4** | Answers the user rated unhelpful | — | **< 15%** | In-product feedback |
| **S5** | Questions the assistant correctly declined rather than guessed | — | **> 90% of out-of-scope questions** | Sampled review of refusals |

**S5 is the one we would defend hardest.** A product that answers everything is worse
than one that answers less and says so. The failure this product must not have is a
confident answer to a question the corpus cannot support.

---

# 6. Assumptions and open questions

## Assumptions we are proceeding on

| # | Assumption | If it is wrong |
|---|---|---|
| A1 | The current policy set can be exported as documents we can index | The product has no corpus and the concept fails |
| A2 | Staff will phrase questions in natural language rather than keywords | Retrieval quality falls; we would need query assistance |
| A3 | Showing the source section is enough for a user to trust the answer | We would need document preview, which is materially more work |
| A4 | Policy documents change slowly enough that a periodic re-index is sufficient | We would need change-triggered ingestion |
| A5 | A wrong answer that is clearly cited is recoverable; a wrong answer with no citation is not | Citations move from important to mandatory before any release |

## Open questions

| # | Question | Owner | Needed by |
|---|---|---|---|
| Q1 | Who owns the corpus once live — Compliance or Operations? | COO | Before release |
| Q2 | Must every answer be retained for audit, or only those acted on? | Compliance | Before the audit feature |
| Q3 | Do we show the user's question to anyone else, and for how long is it kept? | Privacy | Before release |
| Q4 | What happens when two policies conflict — refuse, or show both? | Compliance | Before general availability |

**Q4 is not a technical question, and we should resist the temptation to answer it in
code.** Conflicting policy is a governance problem the bank has today; the product
should surface it, not resolve it.

---

# 7. Scope

## In scope

- Ask a question in natural language and receive an answer
- Every answer shows which policy sections it drew on
- Refuse questions the corpus cannot support, rather than guessing
- Conversation continuity — follow-up questions in context
- A record of what was asked and answered, retrievable afterwards
- Staff can say whether an answer helped
- Ingesting the policy corpus and re-indexing it when documents change

## Out of scope

| | Why |
|---|---|
| Editing or authoring policy | The assistant reads; Policy Office writes |
| Deciding whether an exception is permitted | Judgement stays with humans, by design |
| Customer-facing use of any kind | Internal staff tool only |
| Integrating with case management or the CRM | Later, if the product earns it |
| Answering from anything other than the approved corpus | No web search, no general knowledge |
| Non-English policy documents | Aldermere's policy set is English-only |

---

# 8. Dependencies, risks and constraints

## Dependencies

| | |
|---|---|
| The policy corpus, exported and cleared for indexing | Policy Office |
| A model provider with an approved commercial agreement | Procurement |
| Somewhere to host it | Platform |

## Risks

| Risk | Impact | What we do about it |
|---|---|---|
| **The assistant answers confidently and wrongly** | **Severe** — worse than the current state, because it carries an air of authority | Refusal behaviour is a first-class feature, not an afterthought. Every answer is cited so a user can check it |
| A user treats an answer as a decision | High | The product states what it does and does not do, on every answer |
| The corpus goes stale and nobody notices | High | Re-index on a schedule; surface the indexed date with every answer |
| A user's question contains personal or client data | Medium | Question text is treated as sensitive from the start; retention is decided before release, not after |
| Retrieval is good enough in demos and poor in practice | Medium | A fixed evaluation set of real questions, run on every change |

## Constraints

- **Fictional and sanitised data only.** No real customer information at any point.
- Internal network access only once live.
- The deterministic parts of the product — ingestion, validation, storage, audit —
  must work whether or not the model provider is reachable.

---

# 9. Does AI belong in the runtime? ⭐

**This decision is made deliberately and recorded, because the answer is often no.**

The question is not *"could we use a model here?"* but *"does this product still make
sense if we don't?"*

**Our answer: yes, AI belongs here — for one job only.**

| Job | Who does it | Why |
|---|---|---|
| Understanding a question phrased in someone's own words | **Model** | The whole problem is that staff don't know the policy's vocabulary. Keyword search already exists and already fails |
| Finding the relevant policy sections | **Retrieval, deterministic** | Embedding search over an approved corpus. Repeatable and inspectable |
| Composing an answer from those sections | **Model** | Turning three clauses into one readable paragraph is genuinely language work |
| Deciding whether the answer is supportable | **Rules, deterministic** | If retrieval returns nothing above threshold, the product refuses. **A model does not get to decide whether it knows something** |
| Storing, auditing, exporting, rate-limiting | **Deterministic** | No judgement involved |

**The boundary that matters:** the model *reads and writes language*. It does not
decide what policy says, whether an answer is trustworthy, or whether to answer at
all. Those are rules.

**What this obliges us to do**, because AI is in the runtime:

- A fixed evaluation set of questions with known-good answers, run on every change
- Version the prompt alongside the code, so an answer can be traced to what produced it
- Monitor answer latency, cost and refusal rate
- **A kill switch.** If the model provider degrades, the product must fall back to
  showing retrieved policy sections without a composed answer — **less useful, still
  honest, still working**

That last point is the test of this decision. *If turning the model off leaves nothing
behind, the product was never anything but the model.* Here, turning it off leaves a
working policy search. That is why the decision is defensible.

---

# 10. The thin vertical slice

Everything above describes the product. **This is what gets built first**, and it is
deliberately much smaller.

> **A staff member types one question, and receives one answer citing the policy
> sections it came from — or a refusal if the corpus cannot support one.**

| In the slice | Not in the slice |
|---|---|
| One question, one answer | Follow-up questions in context |
| Citations shown with the answer | Clickable, deduplicated citation panel |
| Refusal when retrieval finds nothing | Tuned confidence thresholds |
| The corpus ingested and searchable | Automatic re-indexing on change |
| Deployed and reachable | Authentication and per-user history |

**Why this slice.** It proves the only thing genuinely uncertain: whether retrieval
over this corpus produces answers a staff member would trust. Everything else —
history, feedback, export, guardrails — is ordinary product work that carries no
learning. If the slice fails, the product concept fails, and better in week one than
after six.

---

# 11. What we are building

## Shape

```
Staff member ──▶ Web interface ──▶ API ──▶ retrieval ──▶ policy corpus
                                     │                     (indexed)
                                     └──▶ model ──▶ answer + citations
                                     │
                                     └──▶ record of the exchange
```

## Front end

A single conversational page. Ask a question, read the answer, see the sources.
No navigation, no dashboard, no settings — **one screen that does one thing.**

The interface must make three things unmissable: **where the answer came from**, that
it is an answer *about policy* and not a decision, and when the assistant has
**declined** rather than answered.

## Back end

An API that accepts a question and returns an answer with its sources. Behind it:

| | |
|---|---|
| **Ingestion** | Load policy documents, split them into passages, embed them |
| **Retrieval** | Find the passages most relevant to a question |
| **Generation** | Compose an answer from those passages, and only from those passages |
| **Refusal** | When nothing retrieved is relevant enough, say so and stop |
| **Record** | Store what was asked, what was answered, and which sources were used |

## Data

Policy documents and their passages. A record of every exchange. Feedback on answers.
**Nothing about a customer, ever.**

## Build and release

- Every change arrives by pull request
- Automated checks run on every push: tests, security scan, dependency licensing
- **Nothing merges without those checks passing and a named human approving**
- Merging to the main branch deploys automatically
- A deployment that fails its health check does not receive traffic
- Any release can be reversed by reverting the change that caused it

**That last group is not infrastructure detail. It is part of the product**, because
a policy tool that cannot say what version answered a question is not fit for a bank.

---

# 12. What success looks like on day one

A member of operations staff, who has never seen this before and received no
training, opens one link, types *"what's the approval threshold for a travel expense
claim?"*, and gets a correct answer citing the Travel and Expense Policy section that
says so — in under a minute.

And when they then ask *"can I expense my partner's flight?"*, the assistant tells
them the corpus does not cover it and points them at Compliance, **rather than
inventing something plausible.**

---

## Appendix — how this brief is used in M04

*Not part of the brief. For the instructor.*

This document is the **M04.1 worked example**: it shows a raw concept shaped into a
bounded, testable feature.

| M04.1 field | Where |
|---|---|
| User and business outcome | §2, §4 |
| Current problem and measurable baseline | §3 |
| Value hypothesis and success measures | §5 |
| Assumptions and unresolved questions | §6 |
| In-scope and out-of-scope boundaries | §7 |
| Dependencies, risks and constraints | §8 |
| **The runtime-AI decision** | **§9** |
| The thin vertical slice | §10 |

**Three things worth pausing on when teaching from it:**

1. **§3's last row** — the cost of the current state is wrongness, not slowness. A
   brief that had stopped at "it takes 18 minutes" would have produced a worse product.
2. **§9** — the runtime-AI decision, made explicitly and with a test attached:
   *if you turn the model off, is anything left?*
3. **§10** — the slice is far smaller than the product, and it is chosen to test the
   one genuinely uncertain thing rather than to show the most.

**Next artefact:** `docs/PRD.md` turns this into an engineering contract — acceptance
criteria, non-functional requirements, architecture decisions and an implementation
plan.

---

*Policy Assistant · Project Brief v1.0 · Aldermere Bank is fictional · CONFIDENTIAL — Chartered Vectorial*
