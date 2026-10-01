# T1 — Release plan

**Stage:** 05 release
**Releasing:** work/table-2 -> table-2 -> api-table-2 + web-table-2
**Written:** 2026-10-01, before the merge

---

## What is being released

A web page where Aldermere staff type a policy question and get an answer taken only from
the bank's policy documents, with the sections it came from shown underneath — or, when the
documents do not cover the question, a plain "not covered" that says who to ask instead.

**In it:** F1 – F5 — the corpus indexed, retrieval, refusal, composed answers with the kill
switch, `POST /ask`, and the page with its top bar. `/history` and `/corpus` are "coming
soon" pages. Follow-up questions in context (F6) are **not** in it.

## What happens on deploy

1. The merge triggers CI's deploy job: `api-table-2` and `web-table-2` build and roll out.
   Railway routes traffic only once `/healthz` answers, so a failed build leaves the
   current version serving. CI then runs `ci/smoke.py` against the API.
2. On its first start the API finds its Qdrant collection empty and **indexes the corpus in
   the background** — about ten seconds (build decision B). Until `/healthz` shows 130
   passages, questions refuse as if not covered (review F30). **Wait for 130.**
3. The API creates its tables in Postgres on start.

## How we will know it worked

*Within two minutes of the smoke test passing.*

- [ ] `https://api-table-2-production.up.railway.app/healthz` reports `database: reachable`,
      `vector_store: 130 passages indexed`, and the model configured *(criterion 37)*
- [ ] On `https://web-table-2-production.up.railway.app`, **"What is the approval threshold
      for a travel expense claim?"** answers **£75**, citing Travel and Expense Policy
      **v3.1 §4.2** with document, section, version and status visible *(criterion 34)*
- [ ] **"Does a claim of exactly £75 need approval?"**, asked straight after, is answered
      with the first answer still visible above it *(criterion 35)*
- [ ] **"Can I expense my partner's flight if they travel with me?"** shows the dashed "Not
      covered by the policy corpus" box — not an answer, not an error *(criterion 36)*

Stage 06 then adds the manual check, criterion 20 (Q7 and Q4: every figure is in the cited
sections; no outside regulator named).

## How we would know it did NOT work

| What we would see | What it probably means |
|---|---|
| CI's smoke test fails, deploy red | The new build never became healthy. **The previous version is still live** — nothing to roll back; read the Railway build log |
| `/healthz` shows `vector_store` *down*, or fewer than 130 passages after two minutes | Qdrant unreachable, or the startup index failed (e.g. OpenRouter down) — the API log says which |
| `/healthz` shows `database` *down* | Postgres unreachable; `/ask` returns 503 "cannot be written" |
| The page shows the red **Error** box: "Could not reach the API at https://api-table-2-…" | `API_URL` on the web service or `ALLOWED_ORIGINS` on the API is wrong |
| Q1 refused, or answered without citations | Index empty or partial, or `MIN_SCORE` not what we set (0.517) |
| Q11 **answered** | The threshold is too low in this environment — the failure this product must not have. **Roll back** |

## Rollback

*Commands, not intentions.* `table-2` takes pull requests only, with an approval, so the
revert goes through one — a direct `git push origin table-2` is refused by branch
protection.

**Fastest — GitHub's own button:** open the merged pull request on GitHub → **Revert** →
it opens a revert pull request → the facilitator approves → merge. CI redeploys the
previous version; Railway switches over about 90 seconds after the build.

**Or from the Codespace:**

```bash
git fetch origin
MERGE=$(git log origin/table-2 --merges -1 --format=%H)   # the merge this release made
git show --stat "$MERGE"                                  # check it is the right one
git checkout -b revert/table-2-t1 origin/table-2
git revert -m 1 "$MERGE" --no-edit
git push -u origin revert/table-2-t1
# then open a pull request revert/table-2-t1 -> table-2; the facilitator approves and merges.
# CI redeploys the previous version; about 90 seconds after the build.
```

**Who decides to roll back:** facilitator
**When to roll back without discussion:** Q11 is answered on the live site, or the live
site cannot answer anything for more than ten minutes after the deploy.

**What we cannot reverse:**

- **Questions already sent to OpenRouter.** Anything asked on the live site has left the
  bank (review F10). Rolling back stops new ones; it cannot recall old ones.
- **Rows written to Postgres** — `conversations`, `messages`, `message_citations` and the
  tables themselves stay after a rollback. The previous version does not read them, so they
  are harmless; removing them is a separate, deliberate step.
- **The indexed Qdrant collection** stays populated. Harmless to the previous version; a
  later release finds it full and skips indexing.

---

## Known limits, shipped knowingly

From the review record — accepted or deferred by the team, with reasons there.

| | What a user or operator could hit |
|---|---|
| **F1** | If OpenRouter is down entirely, search fails too: `/ask` returns 503, not degraded passages |
| **F10** | Every question is stored with no expiry and sent to OpenRouter. Fine for this fictional corpus; **Privacy's open question Q3 blocks any use with real staff** |
| **F11** | `/ask` is open to anyone with the URL, with no rate limit — the table's OpenRouter credit is exposed |
| **F25** | Which provider terms govern the question text is not recorded; the brief's Procurement dependency is open |
| **F28** | A model that hangs keeps the user waiting about three minutes before degraded mode (timeouts stay at PRD §8's 60 s × 3) |
| — | Answered median was 6.9 s locally against NFR-1's 5 s; the refusal threshold sits in a 0.032-wide gap measured on 13 questions |

**For the team checking it:** your network did not resolve `*.app.github.dev`. If
`*.up.railway.app` is blocked the same way, run the stage 06 checks from a phone hotspot.

---

## Evidence — filled in at stage 06

| | |
|---|---|
| Merged at | |
| Deploy finished | |
| Live URL | https://web-table-2-production.up.railway.app |
| Answered a real question | yes / no |
| Refused correctly | yes / no |
