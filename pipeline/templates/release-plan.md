# T1 — Release plan

**Stage:** 05 release
**Releasing:** work/table-N -> table-N -> api-table-N + web-table-N

---

## What is being released

<One sentence a non-engineer would understand.>

## How we will know it worked

*Within two minutes of the deploy.*

- [ ] `/healthz` reports database and vector store reachable
- [ ] <a question the corpus answers> returns an answer with citations
- [ ] <a question it cannot answer> returns a refusal

## How we would know it did NOT work

- <the symptom we would actually notice>

## Rollback

*Commands, not intentions.*

```bash
git revert -m 1 <merge-commit-sha>
git push origin table-N
# Railway redeploys the previous version in about 90 seconds
```

**Who decides to roll back:** <name>
**What we cannot reverse:** <anything irreversible, or "nothing">

---

## Evidence — filled in at stage 06

| | |
|---|---|
| Merged at | |
| Deploy finished | |
| Live URL | |
| Answered a real question | yes / no |
| Refused correctly | yes / no |
