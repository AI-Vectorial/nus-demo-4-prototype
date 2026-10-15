# T1 — Release plan

**Stage:** 05 release
**Table:** 1
**Releasing:** work/table-1 -> table-1 -> api-table-1 + web-table-1
**Gate:** rollback written before merge (this file). **Nothing merges until MSV approves the pull request.**

---

## What is being released

A staff member can type a policy question and get a cited answer from Aldermere's policy documents. If the policies don't cover the question, the product says so and points to Group Finance. It never answers from anything outside the policy set.

## Features in this release

| Feature | In release | Note |
|---|---|---|
| F1 ingest | yes | 130 passages from 5 documents |
| F2 retrieve | yes | Current policies ranked ahead of superseded ones |
| F3 refuse | yes | Threshold `MIN_SCORE` = 0.518 |
| F4 generate | yes | Degraded mode when the model is off or unreachable |
| F5 ask + UI | yes | |
| F6 follow-up | yes | Uses the last 5 user turns (D8, D9) |
| F7 corpus browser | yes | Top bar shows Corpus |
| F8 history | yes | Top bar shows History |

**Cut:** none. F6, F7 and F8 all shipped.

## Known limits, stated plainly

- **Latency (NFR-1) misses its target.** Answers take about 9 to 12 seconds against a p50 target of 5. MSV accepted this (Option B).
- **Slow model returns passages, not an answer (F12).** Each answer has a 25 second budget. If the model is slower, the product returns the retrieved passages with a degraded flag and no composed answer. A slow answer is no longer a 504.
- **Refusal margin is thin.** Answerable Q3 scores 0.526 and refused Q11 scores 0.510, a gap of 0.016. Tuned on 13 questions only.
- **Question text is stored and sent to the model.** Retention accepted by MSV (review F3). Q3 remains open for the product owner.
- **Not yet verified:** NFR-2 (refusal latency, one sample), NFR-4 (ingest timing), NFR-5 (health with Qdrant down), NFR-6 (secrets, scan clean in repo), the citation-to-section link in the browser.
- **Conflict Q10:** the product surfaces both Outsourcing 6.4 and Records Retention 4.1. It does not choose a winner (D6 stays open).

## How we will know it worked

*Within two minutes of the deploy.*

- [ ] `GET /healthz` on `api-table-1` reports database and vector store reachable
- [ ] "What is the approval threshold for a travel expense claim?" returns `outcome: answered` with citations, including the v3.1 section
- [ ] "Can I expense my partner's flight if they travel with me?" returns `outcome: refused` with Group Finance named, and no model call
- [ ] The top bar shows Reset, History and Corpus, and each opens a page

## How we would know it did NOT work

- `/healthz` reports a dependency down, or the vector store shows 0 passages
- A high share of `outcome: degraded` answers while the model is up (the 25 second budget may be too tight for the provider's current speed; check `exchange outcome=` in the logs)
- Any 504 from the API
- Every question returns `503` or `degraded` when the model is up
- A refusal answers a question instead of refusing
- A citation appears without its status, or superseded v3.0 is not flagged
- Any top-bar action leads to a page that doesn't exist

## Rollback

*Commands, not intentions.*

```bash
# 1. Find the merge commit on table-1 for this release
git log --oneline --merges origin/table-1 | head -3

# 2. Revert it, keeping the parent line
git checkout table-1
git pull --ff-only origin table-1
git revert -m 1 <merge-commit-sha> --no-edit
git push origin table-1

# 3. Railway redeploys the previous version (about 90 seconds).
#    Confirm the rollback:
curl -s https://api-table-1-production.up.railway.app/healthz
```

**Data:** conversations already stored in `table_1` are kept. Rolling back the code does not delete them. The `messages` and `message_citations` tables are unchanged by a code revert.

**Re-index:** if the rollback needs a different embedding model or dimension, run `python -m app.ingest --force` after reverting the configuration. Not needed for a plain code revert.

**Who decides to roll back:** MSV (release approver).

**What we cannot reverse:** the stored questions and answers already written to the database. A code revert does not remove them. Deleting them would be a separate, deliberate action.

---

## Evidence — filled in at stage 06

| | |
|---|---|
| Merged at | |
| Deploy finished | |
| Live URL | |
| Answered a real question | |
| Refused correctly | |
| Degraded mode demonstrated on deployed URL (criterion 5) | |
