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
  15min        20min        60min        20min         10min        15min
                 │                                                     │
          ⚠️ HUMAN GATE                                        ⚠️ HUMAN GATE
       your plan is approved                                 your release is
            or rejected                                     approved, then merges
```

Open **`pipeline/01-shape.md`** and read it. Each stage says what to give your
agent and what has to be true before you move on.

## What each stage leaves behind

Every stage produces **a file you can point at.** That is deliberate: at 2:15 somebody
will ask you to show your work, and "we talked about it" is not an artefact.

| Stage | What you get | Why it exists |
|---|---|---|
| **01 shape** | `tickets/T0-alignment.md` | **What the agent thinks you are building, before it builds any of it.** Five lines, the scaffold map, the commands, and the ten §10 decisions listed *unanswered*. You read it and correct it — at minute three, when correcting it is free |
| | `tickets/T1.md` + `T1-F1..F8` | the epic carries **your** acceptance criteria; the children carry the tracking |
| **02 plan** | `tickets/T1-plan.md` | the ten decisions **with your reasons next to them**, the build order, and the riskiest part. ⚠️ a human approves or rejects it |
| **03 build** | working code, committed per feature | each feature's child ticket set to `done` with the command and output that prove it |
| **04 review** | `tickets/T1-review.md` | five passes, and **a decision on every finding** — fixed, accepted or deferred, with a reason |
| **05 release** | `tickets/T1-release.md` + one PR | the rollback, **written before the merge** |
| **06 verify** | a live URL, evidence in the ticket | ⚠️ a human approves, then it deploys |

> ### Why the alignment document exists
>
> It is the cheapest gate in the day. A misunderstanding caught at minute three costs a
> sentence; the same misunderstanding caught at the release gate costs the session.
>
> It does two more things quietly. **Stages 02–06 read it instead of re-reading the PRD,
> the brief and the feature list** — one short corrected file beats three long ones, and
> on a slow agent that is minutes back per stage. And it **lists the ten decisions
> unanswered on purpose**: if a value for one later turns up in the plan, you can see
> exactly where it came from. That is the finding the plan gate exists to produce.

---

**You do not paste prompts.** Read the stage file, then tell your agent:

```
Follow the prompt in pipeline/01-shape.md
```

It opens the file and follows the block itself. Read the file anyway — the checklist
at the bottom of each stage is yours to run, and nothing downstream checks it for you.

---

## 4. What you are building

The corpus is already written — five Aldermere Bank policy documents in
`backend/corpus/`. **It is not indexed.** Indexing it is the first thing you build.

```
F1 ingest ──▶ F2 retrieve ──▶ F3 refuse ──▶ F4 generate ──▶ F5 ask + UI
                                                                 │
                                ┌────────────────────────────────┘
                                ▼
         F6 follow-up ──▶ F7 corpus browser ──▶ F8 history    cuttable
                                │
                                ▼
                     ONE PULL REQUEST ──▶ merged ──▶ DEPLOY
```

**The whole product is the target — all eight, in one pull request at stage 05.**
Deploy is the last thing that happens.

Four routes: **`/`** the assistant, **`/history`** past conversations,
**`/corpus`** the documents, **`/corpus/[id]`** one of them. A **top bar**
carrying **Reset**, plus **History** and **Corpus** once those routes exist —
**never a button that goes nowhere.** It is what makes a half-built product look
half-built.

**Light theme only. No settings page.** Both are explicitly out of scope.

**Short on time? Cut F8, then F7, then F6** — and take their buttons out with
them. A smaller product that is whole beats a bigger one with holes.

---

## 5. Done means this

> **All six stages completed, and a working increment deployed to your own URL.
> Not a finished chatbot.**

You are aiming at F1–F8. You are **marked** on the six stages. The two are not
the same thing, and when they pull against each other the stages win.

A team that ships F1–F5 and cuts the rest has still shaped a ticket, defended a
plan to a human, built against their own acceptance criteria, reviewed in five
passes, written a rollback and released through a gate.

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
