# M04 Lab — Coverage Map

## What the module asks for, and what this repo actually does

| | |
|---|---|
| **Module** | M04 — AI-Native Development Lifecycle: From Concept to Production |
| **Assessed against** | `CV-NUS_M04.6_Coverage_Brief` (the governing spec) and `CV-NUS_M04.5_Coverage_Brief` |
| **Assessing** | This repository as it stands — `pipeline/`, `docs/`, `scripts/`, the reference build |
| **Version** | **3.0** |
| **Supersedes** | v2.0 (`docs/v2/`), which audits a design this repo no longer has — eight stages, five gates, five physical cards, an `/evidence` route. **None of that exists.** v2 should not be used to judge coverage |
| **Date** | 8 October 2026 |

---

# The headline

> **M04.5 — Production Readiness and Controlled Release — is ON HOLD** while the
> Module-5 boundary is reviewed. The M04.6 brief says what that means:
>
> *"Because M04.5 is on hold, this lab carries the release-and-deploy evidence
> itself, at the awareness depth the outline sets."*

So deployment is not a bonus in this lab. **It is a learning outcome the lab has
inherited**, and it is the reason stage 05 and stage 06 exist in the shape they do.

---

# 1. The six phases

The brief runs one 150-minute sprint across six phases. We run six stages across
the same 150 minutes. They line up, with one distortion worth naming.

| Brief phase | Min | Our stage | Min | |
|---|---|---|---|---|
| 1 · Brief and role assignment | 12 | Open | 10 | ⚠️ **no role assignment** |
| 2 · Engineering contract and plan | 25 | 01 Shape + 02 Plan | 35 | ✅ +10 |
| 3 · Build and test | 50 | 03 Build | 60 | ✅ +10 |
| 4 · Independent review and release decision | 25 | 04 Review | 20 | ✅ −5 |
| 5 · Deploy and validate | 18 | 05 Release + 06 Verify (part) | ~18 | ✅ |
| 6 · Showcase and structured debrief | 20 | 06 Verify (remainder) | ~7 | ⚠️ **squeezed** |
| | **150** | | **150** | |

> **The distortion.** The brief protects two phases: *build and test* and *the
> structured debrief* — "cutting either turns a capstone into a demo." We have
> over-weighted build by ten minutes and taken it out of the debrief. The debrief
> is where **LO6** lives, and LO6 is the only outcome the lab adds on its own.
>
> **See gap G4.**

---

# 2. The ten required outputs — the pass condition

The brief is explicit: *"a team passes on the evidence, not just on whether the
app runs."* These ten are the pass condition.

| # | Required output | Status | Where it comes from |
|---|---|---|---|
| 1 | One-page feature shape | 🟡 **PARTIAL** | Provided as `docs/PRD.md` + `project-brief.md`, not produced by the team. They confirm and scope it in stage 01. **By design** — producing it would cost 25 min we do not have. See G5 |
| 2 | Acceptance criteria + essential NFRs | ✅ **FULL** | `tickets/T1.md`, in the team's own words. Stage 01 forbids the agent writing them. They choose which of NFR-1…6 become criteria |
| 3 | Lightweight architecture decision | ✅ **FULL** | D0–D9 in `tickets/T1-plan.md`, each with the team's own reason recorded beside it |
| 4 | Implementation plan | ✅ **FULL** | `tickets/T1-plan.md` — files, order, what they will *not* do, the riskiest part |
| 5 | Working vertical slice | ✅ **FULL** | F1–F5 minimum; F6–F8 cuttable |
| 6 | Automated test evidence | ✅ **FULL** | `pytest` run, not asserted. Stage 03's gate is *"run, not asserted"* |
| 7 | Independent review findings | ✅ **FULL** | `tickets/T1-review.md`, five passes, a decision against every finding |
| 8 | Dependency / provenance record | ✅ **FULL** | **Pass 4 of the review is PROVENANCE & IP** — every dependency, where from, what licence |
| 9 | Release + rollback plan | ✅ **FULL** | `tickets/T1-release.md`. Stage 05's gate: *"a rollback exists, in writing, before anything merges"* |
| 10 | Deployed application | ✅ **FULL** | `web-table-N`, reached by merging the PR |

**Nine of ten clean; one partial by design.** This is the strongest part of the map.

---

# 3. The five acceptance criteria

The outline's own success criteria for the lab:

| Criterion | Status | Evidence |
|---|---|---|
| The slice satisfies its acceptance criteria, and the team can show the evidence used to accept it | ✅ | Stage 06 gate question 2 and 3 |
| **At least one AI output was reviewed critically rather than accepted automatically** | ✅ | The planted defect in `docs/review-example/expense_rules.py`, plus the team's own five passes |
| Security, maintainability and provenance were considered | ✅ | Review passes 2, 3 and 4 |
| The release has an owner, a validation step and a rollback or safe-disable path | 🟡 | Validation ✅ and rollback ✅ are strong. **An owner is not named anywhere.** See G1 and G7 |
| The team can explain where AI helped, where it moved work, and what control caught risk | ✅ | The closing question, verbatim from the brief |

---

# 4. Deployment — what the lab actually teaches

**This is the question worth being precise about: no table writes any CI/CD.**
The scaffold ships it. What a table *does* is produce release evidence and run
the control flow — which is exactly what the brief asks for, and nothing more.

M04.5's controlled-release flow, against our stages:

| Brief step | Ours | |
|---|---|---|
| **Change approval** *(the human gate)* | A different person approves the PR. Branch protection enforces it — a table **cannot** approve its own | ✅ |
| **Deploy** | Merging to `table-N` is the deploy. Railway watches `refs/heads/table-*`. A push to `work/table-N` never deploys | ✅ |
| **Validate + smoke** | `/healthz` for dependencies, then a real question and a real refusal on their own URL — *watched, not reported* | ✅ |
| **Confirm against the original success measures** | Stage 06 question 2: *"read me your acceptance criteria — in your words"*, then demonstrate against them | ✅ |
| **Rollback / safe-disable** | Written before merge. Revert the merge → CI redeploys the previous image. The kill switch is a second safe-disable | ✅ |

And M04.5's production-readiness evidence:

| Evidence item | Status | |
|---|---|---|
| Build and deployment pipeline | ✅ | `.github/workflows/ci.yml` — four checks, then deploy on merge |
| Environment and configuration management | ✅ | Stage 03 rule: *"configuration comes from the environment, not from literals."* Railway service variables |
| Secrets, identity and access | ✅ | Per-table Codespaces secret → `OPENROUTER_API_KEY`. Nothing in the repo |
| Database / schema migration safety | 🟡 | `ensure_database()` / `ensure_tables()` are self-healing, but migration as a *concept* is never discussed |
| Health checks and deployment validation | ✅ | `/healthz` gates the Railway rollout — a failed build cannot take a site down |
| Logs, metrics, traces, SLOs | 🔴 | Logging exists; **metrics, traces and SLOs do not.** See G7 |
| Operational ownership, support, escalation | 🔴 | **Nobody is named as the owner of a deployed table app.** See G7 |
| Rollback | ✅ | Gate of stage 05 |

**Runtime-AI obligations** (M04.5 Topic 3, awareness depth) — better covered than
expected, because the product genuinely has runtime AI:

| | |
|---|---|
| Golden-set / regression evaluation | ✅ `EVALUATION.md`, re-run whenever D0/D1/D2 change |
| Prompt and model versioning | ✅ `answer.v1.md`; every exchange stores its model and prompt version |
| Guardrails and human escalation | ✅ Refusal before any model call; D5 names the owning team |
| Kill switches and safe degradation | ✅ Generation off → passages still returned, flagged |
| Quality, latency and cost monitoring | 🟡 Latency is an acceptance criterion; cost and quality are not monitored |
| Model, data and context drift | 🔴 Not covered. Awareness depth only — acceptable |

---

# 5. Learning outcomes

| | Outcome | Status |
|---|---|---|
| LO1 | Shape | ✅ Stage 01 |
| LO2 | Executable engineering contract | ✅ Stage 01 + 02 |
| LO3 | Direct an agent through implementation | ✅ Stage 03 |
| LO4 | Prove it — test, review, govern, provenance | ✅ Stage 04, five passes |
| LO5 | **Release with production-readiness evidence** | 🟡 Strong on config, secrets, health, validation, rollback. **Thin on observability and ownership** |
| LO6 | **Evaluate where AI reduced, displaced or risked — from evidence** | 🟡 The question is asked, verbatim. **The time to answer it properly is not there.** See G4 |

---

# 6. Gaps — decisions, not surprises

### G1 · No role assignment, and no role cards 🔴

The brief's Phase 1 is *"select the candidate app; assign **product/architecture,
development, testing/platform and risk/review** responsibilities"*, and the role
cards are a **required printed material**: *"one set per team."*

We have none. Tables self-organise around one keyboard.

**Why it matters beyond compliance.** The brief's framing section says *"every
role owns a lane"* — and the cohort is deliberately mixed (developers,
architects, QA, platform, risk). Without lanes, the two developers at each table
drive and the risk person watches. That is the single most likely way a table
has a bad afternoon.

**Cost to close:** four role cards, one page each, and two lines in the runbook
at 0:05. Perhaps two hours.

### G2 · No recorded fallback 🔴

*"Must survive a dead venue network — recorded fallback mandatory."* The slip
protocol is explicit: without a rehearsed lab pack two weeks out, you run the
recorded build.

Tracked as **NUS-295**, not done. This is the one gap that is a genuine delivery
risk rather than a quality gap.

### G3 · Only one runbook 🟡

The brief wants **both** modes delivery-ready — hands-on *and* instructor-led —
because the sandbox decision is a programme gate. We have hands-on only.

Mitigated: our sandbox is Codespaces, already cleared, and five Codespaces have
been proven. The instructor-led mode is a contingency for a failure we have
largely engineered out. **Accept, but say so out loud rather than discover it.**

### G4 · The debrief is squeezed 🟡

Brief: 20 minutes for showcase + structured debrief, and it is a **protected**
phase. Ours: about 7, after five tables have each been through a six-question
release gate.

LO6 is the only outcome this lab adds that no other session teaches. Seven
minutes across five tables is 80 seconds each.

**Cheapest fix:** take the ten minutes back from stage 03, which is already ten
over the brief. The build does not need 60; the debrief does need 15.

### G5 · The feature shape is provided, not produced 🟡

Output #1. The team confirms and scopes rather than writes. **Deliberate** — the
PRD is what makes five tables comparable, and writing a feature shape from
nothing is a 25-minute exercise the clock does not have. Worth stating as a
decision in the module-owner review rather than leaving it to be noticed.

### G6 · One candidate app, not five 🟡

The brief lists five candidate apps (Policy Exception, Incident Triage, KYC
Completeness, Expense Claim, Complaint Router) and expects a team to select one.
We give all five tables the same Policy Assistant.

**Deliberate, and arguably better:** five tables building the same thing makes
the *decisions* the only variable, which is what the gates interrogate and what
the showcase compares. Five different apps would make the debrief an
apples-to-oranges exercise. **A deviation to declare, not to fix.**

### G7 · Observability and ownership 🟡

The two weakest items in the M04.5 evidence checklist. No metrics, no traces, no
SLOs, and no named owner for a deployed app.

**Cheapest fix that is honest:** one line in `release-plan.md` — *"who gets
called when this breaks, and how would they know?"* It will not add telemetry,
but it makes the absence a recorded decision rather than an oversight, which is
the lesson anyway.

---

# 7. What is genuinely strong

Worth stating, because the gaps list is longer than the praise list and that is
misleading.

- **The ten outputs.** Nine of ten produced as real artefacts, in the repo, reviewable.
- **Pass 4 is not paperwork.** Provenance and IP is a full review pass, and it has already caught something real on this project.
- **The seeded failure.** The brief asks for *"a likely genuine AI failure … so the debrief has something true to hold."* We have a planted defect that no test catches (`> 75` against a policy that says *£75 or more*), plus natural failures the build reliably produces — threshold drift after an embedding change, superseded passages crowding out current ones.
- **The deploy is a governance act.** No table can deploy. Only a human approving a pull request can. That lands M04.5's key message — *"releasing is not 'it deployed'"* — structurally rather than rhetorically.
- **"Cut scope, never a stage."** The brief's cut list protects build and debrief; ours protects the stages and sacrifices features. Same instinct, stated where a table will actually meet it.

---

# 8. Recommended before delivery

| | Do | Why |
|---|---|---|
| 1 | **Four role cards** (G1) | Required material; also the fix for a mixed-role table |
| 2 | **Record the fallback** (G2 / NUS-295) | The slip protocol depends on it |
| 3 | **Move 10 min from build to debrief** (G4) | LO6 is the lab's own outcome |
| 4 | **One ownership line in the release template** (G7) | Closes the weakest LO5 item cheaply |
| 5 | **Declare G5 and G6 in the module-owner review** | They are good decisions; they should not look like misses |

---

*Coverage Map · v3.0 · assessed against the issued M04.5 and M04.6 briefs · CONFIDENTIAL — CV — NUS AIDF Alliance*
