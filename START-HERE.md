# Start here

**You are building a policy assistant, and deploying it.**

Everything is already running. You do not need to configure anything.

---

## 1. Where you are

| | |
|---|---|
| **Your branch** | `table-N` is yours. Work on `work/table-N` |
| **Your app** | `https://web-table-N-production.up.railway.app` |
| **Your API** | `https://api-table-N-production.up.railway.app` |
| **Already running** | port 3000 the app, port 8000 the API |
| **Also running** | Postgres and Qdrant, in your Codespace. Yours alone |

**Your API key is already in your environment.** So are your database and your
vector store — both running beside you in this Codespace, so you can index the
corpus and watch retrieval work without deploying anything.

Nobody else can reach them, and you cannot reach anybody else's.

---

## 2. Read these three, in this order

| | | |
|---|---|---|
| 1 | `docs/project-brief.md` | why this product exists |
| 2 | **`docs/PRD.md`** | **what must be true. The contract** |
| 3 | `docs/features.md` | what to build first |

> **PRD §10 is the one to read twice.** Ten decisions are deliberately left to
> you — chunk size, the refusal threshold, how much conversation a follow-up
> sees, what happens when two policies contradict each other. **You will be
> asked to defend your answers**, and *"the agent chose it"* is a failed answer.

---

## 3. The six stages

```
01 shape ──▶ 02 plan ──▶ 03 build ──▶ 04 review ──▶ 05 release ──▶ 06 verify
  15min        25min        60min        25min         10min        15min
                 │                                                     │
          ⚠️ HUMAN GATE                                        ⚠️ HUMAN GATE
       your plan is approved                                 your release is
            or rejected                                     approved, then merges
```

Open **`pipeline/01-shape.md`** and follow it. Each stage says what to give your
agent and what has to be true before you move on.

---

## 4. What you are building

The corpus is already written — five Aldermere Bank policy documents in
`backend/corpus/`. **It is not indexed.** Indexing it is the first thing you build.

```
F1 ingest ──▶ F2 retrieve ──▶ F3 refuse ──▶ F4 generate ──▶ F5 ask + UI ──▶ DEPLOY
                                                                  │
                                           F6 follow-up ◀─────────┘
                                           F7 corpus browser
                                           F8 history
```

Four routes: **`/`** the assistant, **`/history`** past conversations,
**`/corpus`** the documents, **`/corpus/[id]`** one of them. A **top bar** with
three actions: **Reset**, **History**, **Corpus**.

**Light theme only. No settings page.** Both are explicitly out of scope.

**Deploy the moment F5 works.** Do not wait to be finished.

---

## 5. Done means this

> **All six stages completed, and a working increment deployed to your own URL.
> Not a finished chatbot.**

A team that ships ingestion and retrieval but runs out of time before generation
has still shaped a ticket, defended a plan to a human, built against their own
acceptance criteria, reviewed in five passes, written a rollback and released
through a gate.

**That is the whole exercise.** A polished chatbot with no review record is the
worse outcome — so if you are running short, **cut scope, never a stage.**

---

## 6. Three things you cannot do

| | |
|---|---|
| Edit `docs/`, `pipeline/`, `ci/`, `.github/` or **`backend/corpus/`** | CI refuses the build |
| Push straight to `table-N` | Pull request only, and it needs an approval |
| Let your agent decide a PRD §10 question for you | It is your decision, and you will be asked |

> **The corpus is the one you will be tempted by.** When retrieval performs
> badly, editing a policy document so it contains the words you searched for
> makes the demo work and the product worthless. **Fix retrieval.**

---

## 7. If something breaks

| | |
|---|---|
| Tests failing | `cd backend && pytest -q` — read the failure before changing anything |
| API unreachable | `curl localhost:8000/healthz` — it reports every dependency |
| CI red | Click **Details** on the check. The message says what and why |
| Deploy red | **Your live site is unaffected.** Railway does not route traffic to a build that failed its health check |
| Stuck for ten minutes | **Ask an instructor.** That is what they are there for |

---

**Now open `pipeline/01-shape.md`.**

---

*Policy Assistant · M04 · Aldermere Bank is fictional*
