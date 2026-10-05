# Stage 06 — Verify

**~15 minutes. It works on your URL, or it does not work.**

---

## Inputs

The pull request from stage 05, carrying the whole increment · your deployment at
`web-table-N`

## Output

Evidence recorded in `tickets/T1-release.md`, and a working URL.

## The gate

> **The application answers a real question on the live URL — watched, not reported.**

---

# The release gate

The release manager asks five questions. **Answer them from your artefacts, not from
memory.**

| | |
|---|---|
| 1 | Show me your ticket |
| 2 | Read me your acceptance criteria — **in your words** |
| 3 | Show me the test that was red and is now green |
| 4 | **Which review finding did you accept, and why?** |
| 5 | How do we get this back if it is wrong? |
| 6 | **What did you cut, and does the interface still offer it?** |

All six answered → **approved → merge → it deploys.**

> **Question 6 is why deploy waits until here.** Cutting F6, F7 or F8 is a legitimate
> answer and nothing is lost by it. A top bar still advertising a screen that was cut is
> a different thing — the product claiming something that is not there — and the last
> moment to catch it is before it is live.

---

## After the merge

**This is the deploy.** Nothing went out at F5 and nothing went out when the PR opened;
the merge is the first time any of it is on a URL.

```
merge to table-N  ──▶  CI deploys  ──▶  api-table-N + web-table-N
                                              │
                                        about 90 seconds
```

**Then, on your own URL:**

- [ ] `/healthz` reports database and vector store reachable
- [ ] Ask a question you know the corpus answers — **it answers, with citations**
- [ ] Ask a question you know it cannot — **it refuses, and says where to go instead**
- [ ] A citation shows its document, section and version
- [ ] Every action in the top bar opens something — **and anything cut is not offered**

> **Show the refusal deliberately.** It is the behaviour this product is judged on, and
> the one nobody expects to be impressed by until they watch it work.

## If the deployment fails

That is a real outcome, not a disaster. Check the CI logs, check `/healthz`, check the
service variables.

**If it cannot be fixed in the time left, execute the rollback from your release plan —
and say so out loud.** *"We shipped something wrong, we noticed, and we reversed it in
two minutes"* is a better story than a clean run, and a more useful one for the room.

---

# The debrief

**Twenty minutes, and it is not optional.** Each team answers three questions honestly.

| | |
|---|---|
| **Where did AI reduce effort?** | Concretely. Which part would have taken longer by hand? |
| **Where did it displace effort, or introduce risk?** | Reviewing generated code is work too. What did you have to undo, correct, or check that you would not otherwise have needed to check? |
| **⭐ What control caught a weak output before it reached production?** | The scope check, a failing test, the licence check, a rejected plan, a review finding — **name it** |

> **A blank middle column is a red flag, not a clean run.** If nothing displaced effort
> and nothing introduced risk, the team was not looking hard enough. The honest
> accounting is the point — and the third column is the reason the gates exist at all.

## Before you finish

- [ ] The PR is merged and the deployment succeeded
- [ ] The URL answers a real question, with citations
- [ ] It refuses a question it should refuse
- [ ] Ticket, plan, review record and release plan are all committed
- [ ] The team can name **the control that caught something**
