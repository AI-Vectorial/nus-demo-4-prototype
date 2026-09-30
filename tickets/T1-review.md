# T1 — Review record

**Stage:** 04 review
**Branch:** work/table-2 (diff against `origin/table-2`: 35 files, +1411 / −245 in `backend/app` and `frontend`)
**Reviewed:** 2026-09-30

*Five passes, run separately. Every finding gets a decision — made by the team, not the agent.*

---

## Pass 1 — Correctness

*Does it do what the ticket says? Edge cases, boundaries, empty, null, huge.*

Findings F1 – F9, decided 2026-09-30: the team replied "go with your recommendations", was shown each one, and replied **"confirm"** — so the reasons below are the agent's recommendations, confirmed by the team. The acceptance criteria all pass; these are the places where passing the
criteria and doing what the ticket means come apart.

## Pass 2 — Security and privacy

*Not yet run.*

## Pass 3 — Maintainability

*Not yet run.*

## Pass 4 — Provenance and IP

*Not yet run.*

## Pass 5 — Production fitness

*Not yet run.*

---

## Findings

### F1 — The kill switch does not survive a full provider outage
**Pass:** 1
**Severity:** high
**Where:** `backend/app/retrieve/retrieve.py:50`, `backend/app/api/ask.py` (the 503 branch)
**What:** Embeddings come from OpenRouter too. If OpenRouter is unreachable, the question
cannot be embedded, retrieval cannot run, and `/ask` returns a 503 error — not the degraded
"passages without an answer" REQ-G6 promises "when the provider is unreachable". Criterion
18 only simulated the *chat* model failing. The brief §9 test — "turn the model off and a
working policy search is left" — holds for `GENERATION_ENABLED=false`, not for an outage.
**Options:** fixing needs a search path that does not use the provider (a local embedding
model or keyword search) — a new dependency and new scope. Or record it honestly.
**Agent's recommendation:** DEFERRED — name it as a known gap in the release plan.
**Decision:** DEFERRED — fixing needs a search path that does not use the provider (a new dependency and new scope). Named as a known gap in the release plan.

### F2 — A half-finished first index is never completed
**Pass:** 1
**Severity:** medium
**Where:** `backend/app/main.py:69`
**What:** Startup indexing runs only when the collection is empty. The corpus embeds in two
batches (96 + 34). If the first boot fails after batch one, 96 passages are stored; every
later start sees a non-empty collection and skips. The missing 34 sections then refuse
forever, with nothing saying why.
**Fix:** compare the stored count to the number of passages the corpus produces (no model
call needed) and re-run the idempotent ingest when they differ.
**Agent's recommendation:** FIX — small, and it is the path the live deploy depends on.
**Decision:** FIXED — to be applied after pass 5: re-run the idempotent ingest on startup when the stored count differs from the corpus.

### F3 — An empty model reply is shown as an answer
**Pass:** 1
**Severity:** medium
**Where:** `backend/app/features/ask.py:81`
**What:** If the model returns an empty string (reasoning models occasionally do), the
outcome is `answered` with empty text: an empty answer box above citations, recorded as
answered.
**Fix:** treat an empty or whitespace-only reply as `degraded`.
**Agent's recommendation:** FIX.
**Decision:** FIXED — to be applied after pass 5: an empty or whitespace-only reply becomes `degraded`.

### F4 — Citations list every passage the model was given, not only the ones it used
**Pass:** 1
**Severity:** medium
**Where:** `backend/app/features/ask.py:74`
**What:** Q1 cited five sections, including two superseded v3.0 sections and two
self-approval sections the answer never mentions. REQ-G3 holds literally — these are the
passages that produced the answer — but a reader may think the superseded sections back it.
**Options:** keep (the Superseded label makes it visible, and it is honest about what the
model saw); or have the model name the passages it used and show only those — which lets
the model decide what counts as a source.
**Agent's recommendation:** ACCEPTED — honest, and the D4 label carries the risk.
**Decision:** ACCEPTED — the list is honest about what the model was given, and the Superseded label carries the risk. Letting the model choose its own sources would move a judgement from code to the model.

### F5 — Splitting an oversized section would flatten its line breaks
**Pass:** 1
**Severity:** low
**Where:** `backend/app/ingest/chunker.py:34`
**What:** When a section exceeds `CHUNK_MAX_TOKENS`, sentences are re-joined with spaces, so
a table or list inside it would lose its rows. Latent: no section is near the cap (largest
≈ 195 words vs 512 tokens).
**Agent's recommendation:** ACCEPTED — record; revisit if the cap is lowered.
**Decision:** ACCEPTED — latent; no section is near the cap. Revisit if `CHUNK_MAX_TOKENS` is lowered.

### F6 — Headings deeper than `###` are not section boundaries
**Pass:** 1
**Severity:** low
**Where:** `backend/app/ingest/loader.py:18`
**What:** A `####` heading would be folded into its parent section's text. The corpus has
none today.
**Agent's recommendation:** ACCEPTED — the corpus is protected and fixed.
**Decision:** ACCEPTED — the corpus is protected and has no `####` headings.

### F7 — The answer renderer understands bullets and bold only
**Pass:** 1
**Severity:** low
**Where:** `frontend/components/Prose.tsx:25-36`
**What:** A numbered list runs together into one paragraph; a table the model writes shows
as raw pipes. Deliberately small, to avoid a Markdown dependency.
**Agent's recommendation:** DEFERRED — to F7, where full Markdown rendering is REQ-U12.
**Decision:** DEFERRED — to F7, where full Markdown rendering is REQ-U12.

### F8 — After a database reset, the open page errors until Reset
**Pass:** 1
**Severity:** low
**Where:** `backend/app/api/ask.py:104`, `frontend/components/Chat.tsx`
**What:** The page keeps its `conversation_id`. If that conversation no longer exists, every
question returns 404 and shows the error box ("No such conversation.") until the user
presses Reset.
**Agent's recommendation:** ACCEPTED — rare, and the message plus Reset recovers it.
**Decision:** ACCEPTED — rare, and the message plus Reset recovers it.

### F9 — Criterion 5 is only enforced for split sections
**Pass:** 1
**Severity:** low
**Where:** `backend/tests/features/test_f1_ingest.py`
**What:** Criterion 5 says every passage ends at the end of a sentence. Whole sections end
where the author ended them — often a table row or list item, not a full stop. The test
checks that *splits* happen only at sentence ends, which is what REQ-I2 ("never
mid-sentence") means, but it is narrower than the criterion's wording.
**Agent's recommendation:** ACCEPTED — record the interpretation in the ticket.
**Decision:** ACCEPTED — the test enforces what REQ-I2 means ("never mid-sentence"); interpretation recorded here.

---

## Dependencies

*Pass 4.*

| Package | Version | Licence | Permissive? |
|---|---|---|---|
| | | | |

## Summary

| | |
|---|---|
| Findings | |
| Fixed | |
| Accepted | |
| Deferred | |

**The one we accepted on purpose, and why:**

<This is the question the release manager will ask.>
