# T1 — Release plan

**Stage:** 05 release
**Releasing:** work/table-3 -> table-3 -> api-table-3 + web-table-3

Ticket: [T1](T1.md) · Plan: [T1-plan](T1-plan.md) · Review: [T1-review](T1-review.md) ·
Decisions: [docs/design/](../docs/design/)

---

## What is being released

Aldermere staff can ask a policy question in plain language and get an answer drawn only
from the bank's own policies, showing the sections it came from, or a plain statement that
the policies do not cover it and who owns each policy area.

**Features:** F1 to F8, all of them. **Nothing was cut.**

| | |
|---|---|
| F1 ingest | done (the deployed service builds its own index on boot) |
| F2 retrieve | done |
| F3 refuse | done |
| F4 generate | done (prompt `answer-v2`) |
| F5 ask + UI | done · **C21 known limitation** |
| F6 follow-up | done · **C31 known limitation** |
| F7 corpus browser | done |
| F8 history | done |

**Top bar:** Reset, History and Corpus. Each opens a route this release builds (`/`,
`/history`, `/corpus`), so it offers nothing that does not exist.

## Known limitations the release gate must accept or block

| | What | Decided by |
|---|---|---|
| **C31** | An out-of-scope question asked as a follow-up (Q11 after Q1) is **answered, not refused**. The model's text declines, but the outcome is `answered`. No threshold can fix it. | Team: keep C31 and D9 as written, no model-based refusal gate |
| **C21** | Median answer latency was **5.2 s and 6.2 s** in two full runs, against a target of under 5 s. The time is the model call. Refusals take about 1 s (passes). | Team: known limitation for this release |
| S1 | Every question is sent to OpenRouter (embedding and chat). A question can contain personal data. | Accepted under C24 (F10 out of scope) — **confirm** |
| S2 | History (`/conversations`) has no authentication, so anyone who can reach the API can read every conversation. | Accepted under C24 (auth out of scope) — **confirm, or cut F8** |
| F4 | A hung model can hold an answer for minutes (60 s timeout × 3 retries) before degrading. | Deferred, tied to C21 — **confirm** |
| P1 | LGPL-3.0 `sharp` binaries come in under Next.js. They predate T1. | Deferred to the project owner |

Configuration: none to set. The team's decisions (D0 `text-embedding-3-large`/3072, D1
400/0, D2 `MIN_SCORE=0.485`, D3 5, D8/D9 5 messages) are the defaults in
`backend/app/core/config.py`. Railway's existing variables (database, Qdrant, collection,
origins, key) are unchanged.

## How we will know it worked

*Within two minutes of the deploy. API: `https://api-table-3-production.up.railway.app`,
app: `https://web-table-3-production.up.railway.app`.*

- [ ] `/healthz` answers `"status": "ok"`, with `database: reachable` and
      `vector_store: 135 passages indexed`. On the first deploy, the service builds the
      index in the background (a few seconds to about 20 s), so the count may read lower
      for a moment.
- [ ] *"What is the approval threshold for a travel expense claim?"* returns an answer with
      citations, including Travel and Expense Policy v3.1 §4.2. The superseded v3.0 is
      marked as superseded.
- [ ] *"How many days of paid parental leave am I entitled to?"* returns a refusal that
      lists the policy owners.
- [ ] Clicking a citation opens that section in the corpus browser, highlighted.
- [ ] History and Corpus open from the top bar.

```bash
API=https://api-table-3-production.up.railway.app
curl -s $API/healthz
curl -s -X POST $API/ask -H 'content-type: application/json' \
  -d '{"question":"What is the approval threshold for a travel expense claim?"}' | head -c 400
curl -s -X POST $API/ask -H 'content-type: application/json' \
  -d '{"question":"How many days of paid parental leave am I entitled to?"}' | head -c 200
```

## How we would know it did NOT work

- `/healthz` never answers. Railway keeps the previous version live, and CI's smoke test
  fails.
- `vector_store` still says `collection not created yet` or a low count after two
  minutes. The logs then show `index not ensured: <error>` (key, Qdrant or model access).
- Every question is refused: the index is empty or the wrong one.
- `/ask` returns 503 "policy search is unavailable" or "conversation store is
  unavailable": Qdrant or Postgres is unreachable.
- The app says "Could not reach the API": `API_URL` or `ALLOWED_ORIGINS` on Railway.
- Answers appear with no citations, or a superseded section is not marked. That is a
  defect, and we roll back.

## Rollback

*Commands, not intentions.*

```bash
git fetch origin
git checkout table-3 && git pull
git log --merges -1 --format='%H %s'      # the T1 merge commit
git revert -m 1 <merge-commit-sha>
git push origin table-3
# CI runs, the gate passes, Railway redeploys the previous version in about 90 seconds.
curl -s https://api-table-3-production.up.railway.app/healthz   # confirm the old build sha
```

`table-3` is a protected branch. If it refuses the direct push, the revert goes through
the same gate as the release:

```bash
git checkout -b revert/t1 && git revert -m 1 <merge-commit-sha>
git push -u origin revert/t1
gh pr create --base table-3 --head revert/t1 --title "Revert T1" --body "Rollback per tickets/T1-release.md"
```

**Who decides to roll back:** the release manager, who approves this PR. The project owner
or requester can also call it.

**What we cannot reverse:**

- **Questions already asked were sent to OpenRouter.** That cannot be recalled.
- **Conversations stored in Postgres** (`conversations`, `messages`, `message_citations`,
  created by this release) stay after a rollback. The previous version ignores them. If
  they must go, a human runs this deliberately, after a decision, not as part of the
  rollback:
  ```sql
  DROP TABLE message_citations; DROP TABLE messages; DROP TABLE conversations;
  ```
- **The Qdrant collection** `policy_passages_table_3` is rebuilt at 3072 dimensions. It is
  derived from the corpus, and any later version rebuilds it on boot, so nothing is lost.

---

## Evidence — filled in at stage 06

| | |
|---|---|
| Merged at | |
| Deploy finished | |
| Live URL | |
| Answered a real question | yes / no |
| Refused correctly | yes / no |
