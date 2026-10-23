# T1 — Review record

**Stage:** 04 review
**Branch:** work/table-4
**Reviewed:** 2026-10-23 · commit `30e5b05` (F5), diff against `10bb9d4` (F4)

*Five passes, run separately. Every finding gets a decision. Nothing is fixed yet:
the agent recommends, the team decides. Decisions marked **AWAITING TEAM** are not
yet decisions, and this stage does not pass until they are.*

---

## Warm-up (calibration, not part of this record)

Run on `docs/review-example/expense_rules.py` first. Passing tests were not run.
- Pass 1: `> 75` contradicts §4.2 ("75 or more"), so exactly £75 is wrongly auto-approved.
- Pass 2/3: claimant name and email are written to the INFO log.
- Pass 3: `submit()` swallows the store exception with `pass`.

---

## Pass 1 — Correctness

- **FND-1** the answer note for superseded sources is not shown (high).
- **FND-2** citations merge across policy versions (medium).
- **FND-3** follow-up turns are answered without prior context (medium).
- **FND-10** `last_at` is never updated after the first turn (low).

## Pass 2 — Security and privacy

- **FND-4** the question text is kept indefinitely (medium).
- **FND-5** the question has no length limit (medium).

## Pass 3 — Maintainability

- **FND-12** the outcome assignments in `ask()` are repeated (low).

## Pass 4 — Provenance and IP

No findings. The F5 diff adds no dependencies (no changes to `requirements*.txt`,
`pyproject.toml` or `package.json`). `ci/check_licences.py` reports PASS on 60
dependencies, all permissive. I have not read the licence of each transitive
dependency myself.

## Pass 5 — Production fitness

- **FND-6** `/healthz` does not report whether the schema was created (medium).
- **FND-7** a Qdrant error is not caught, so it returns an unhandled 500, unlike the 503 for the model provider (medium).
- **FND-8** the 503 response and the `notice` field are not in PRD §5 (medium).
- **FND-9** the browser has no request timeout, so the pending state can hang (medium).

---

## Findings

### FND-1 — Superseded note is computed but never shown
**Pass:** 1 — correctness
**Severity:** high
**Where:** `backend/app/generate/compose.py` (`SUPERSEDED_NOTICE`), `backend/app/api/ask.py` (`notice`), `frontend/components/Answer.tsx`
**What:** The API returns `notice` when a superseded version is a source. `Answer.tsx` renders only the answer text and citations. PRD decision D4 (`tickets/T1-plan.md`) says the answer states when a superseded version was the source. Without the note, a superseded source appears only as a badge.
**Decision:** AWAITING TEAM. Recommend **FIXED**: render `notice` in `Answer.tsx`. Reason: D4 was accepted and is not met.

### FND-2 — Citations merge across policy versions
**Pass:** 1 — correctness
**Severity:** medium
**Where:** `backend/app/api/ask.py`, `cite()`
**What:** Citations are keyed on `(document_id, section)`, without `version`. Both travel policy versions share headings such as `1.1 Purpose`, `1.2 Who this applies to` and `2.x` (checked in `backend/corpus/`). If the same heading is retrieved from v3.0 and v3.1, one is dropped. If the superseded one scores lower, the withdrawn version disappears, which defeats REQ-U4. Not yet reproduced with a live query.
**Decision:** AWAITING TEAM. Recommend **FIXED**: add `version` to the key, with a test that the same heading from two versions gives two citations.

### FND-3 — Follow-ups are answered without context
**Pass:** 1 — correctness
**Severity:** medium
**Where:** `backend/app/api/ask.py`, `ask()`; `CONTEXT_MESSAGES` is unused
**What:** The route accepts `conversation_id` and stores the turn, but the question is answered alone. REQ-C3 and REQ-C7 are not met. The UI makes it look like a conversation.
**Decision:** AWAITING TEAM. Recommend **DEFERRED to F6**, which the F5 ticket names as out of scope. Reason: F6 is the feature for follow-up context. Until then the UI should not imply context is kept.

### FND-10 — `last_at` is never updated
**Pass:** 1 — correctness
**Severity:** low
**Where:** `backend/app/models/record.py`, `Conversation.last_at`
**What:** It is set once on creation. F8 will list conversations newest first (REQ-C8), so the order will be wrong.
**Decision:** AWAITING TEAM. Recommend **DEFERRED to F8**. Reason: nothing reads it until F8.

### FND-4 — Question text is kept indefinitely
**Pass:** 2 — security and privacy
**Severity:** medium
**Where:** `backend/app/models/record.py`, `Message.content`; `backend/app/api/ask.py`
**What:** Every question is stored in Postgres with no retention rule. A question can contain a client name. The brief's open question Q3 has not been answered.
**Decision:** AWAITING TEAM. This is the team's decision, and I am not choosing it. Options: keep as is, add a retention period, or redact. Please decide and give the reason.

### FND-5 — Question length is unbounded
**Pass:** 2 — security and privacy
**Severity:** medium
**Where:** `backend/app/api/ask.py`, `AskRequest.question`
**What:** There is no maximum length. A very long question costs an embedding call and possibly a generation call, and is stored in full.
**Decision:** AWAITING TEAM. Recommend **FIXED**: a maximum length set from the environment (not a literal in code), rejected with 422.

### FND-12 — Repeated outcome assignments in `ask()`
**Pass:** 3 — maintainability
**Severity:** low
**Where:** `backend/app/api/ask.py`, `ask()`
**What:** The tuple assignments for each outcome are repeated across branches, and `latency_ms` is 0 for refusals, which can be misread.
**Decision:** AWAITING TEAM. Recommend **ACCEPTED**: it reads clearly at this size. Reason: a refactor now would not change behaviour.

### FND-6 — Schema failure is not visible on `/healthz`
**Pass:** 5 — production fitness
**Severity:** medium
**Where:** `backend/app/main.py` (lifespan), `backend/app/core/database.py` (`ensure_schema`)
**What:** `ensure_schema()` returns `(False, reason)` on failure. Startup prints it and continues, and `/healthz` does not report it. `/ask` then fails with a 500 that does not name the cause.
**Decision:** AWAITING TEAM. Recommend **FIXED**: report schema state in `/healthz`.

### FND-7 — Qdrant errors are unhandled
**Pass:** 5 — production fitness
**Severity:** medium
**Where:** `backend/app/api/ask.py` (`retrieve_grounded` call); `backend/app/retrieve/qdrant_store.py`
**What:** Only `ProviderError` is caught. A Qdrant failure propagates as an unhandled exception and returns a 500. Not yet tested by stopping Qdrant.
**Decision:** AWAITING TEAM. Recommend **FIXED**, mapped the same way as FND-8 so both are explicit. Depends on FND-8.

### FND-8 — 503 and `notice` are outside the PRD §5 contract
**Pass:** 5 — production fitness (contract)
**Severity:** medium
**Where:** `backend/app/api/ask.py`, `AskResponse`; `docs/PRD.md` §5
**What:** PRD §5 defines three outcomes and no `notice` field. The 503 for an unreachable provider is also not in §5. AGENTS.md §3 makes a contract change a human decision, and `docs/PRD.md` is protected, so I have not changed it.
**Decision:** AWAITING TEAM. Two options: add 503 and `notice` to PRD §5 (the release manager decides), or change the code to fit §5. I recommend adding them to §5, since the behaviour is already accepted in F5.

### FND-9 — No timeout on the browser request
**Pass:** 5 — production fitness
**Severity:** medium
**Where:** `frontend/lib/api.ts`, `request()`
**What:** `fetch` has no timeout. If the API stalls, the pending state never clears and the user cannot tell whether the question was sent.
**Decision:** AWAITING TEAM. Recommend **FIXED**: an `AbortController` timeout that shows the error view.

---

## Dependencies

| Package | Version | Licence | Permissive? |
|---|---|---|---|
| (none added in F5) | | | |

`ci/check_licences.py`: PASS, 60 dependencies, all permissive. Transitive licences not checked individually.

## Summary

| | |
|---|---|
| Findings | 10 |
| Fixed | 0 |
| Accepted | 0 (recommended: FND-12) |
| Deferred | 0 (recommended: FND-3, FND-10) |
| Awaiting team | 10 |

**The one we accepted on purpose, and why:**

<Not yet. Recommended: FND-12. Reason: the outcome logic is clear at this size and a refactor now would not change behaviour. The team decides.>
