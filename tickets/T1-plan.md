# T1 — Implementation plan (reference build)

**Stage:** 02 plan
**Branch:** `reference` → deploys to `api` / `web`
**Status:** APPROVED — decisions delegated by the release manager

---

## The decisions

*PRD §10. Delegated, so the reasons here are mine and open to challenge.*

| # | Decision | Chosen | Why |
|---|---|---|---|
| **D0** | Embedding model / dimensions | `text-embedding-3-small`, **1536** | Verified working through OpenRouter. 3072 doubles storage and cost for a 5-document corpus that is not hard to search. Re-indexing later is cheap; it is one command |
| **D1** | Chunk size / overlap | **section-first**, 400 max, 60 overlap | Policy is already written in numbered sections, and a citation to *"§4.2 Approval thresholds"* is verifiable by a human. Only a section over 400 tokens splits, on paragraph boundaries — so a clause never loses the sentence that qualified it |
| **D2** | Refusal threshold | **0.30**, tuned against `EVALUATION.md` | Starting value. Tuned once the corpus is indexed by running all thirteen questions and taking the value that separates the ten from the three. Recorded with the score distribution |
| **D3** | Passages retrieved | **6** | Enough for a question whose answer spans two sections; few enough that the weakest is still relevant. Above ~8, noise starts pulling answers off-topic |
| **D4** | Superseded policies | **shown, flagged** | REQ-I7 indexes them; hiding them makes *"has this changed?"* unanswerable. Flagged loudly, because an answer citing a withdrawn policy is the exact failure the brief exists to prevent |
| **D5** | What a refusal says | what is not covered **+ who owns it** | *"I don't know"* leaves the user where they started. Every document has an `owner` in its front matter, so the refusal can name a real team |
| **D6** | Conflicting policies | **surface both, name the conflict, do not resolve** | The corpus's retention/outsourcing conflict is a governance problem Aldermere already has. Resolving it in code makes the software decide which policy wins. The prompt is told to present both and say they conflict |
| **D7** | Citation grouping | **one per section, deduplicated** | Two passages from §4.2 are one citation. Grouping by document would lose the section, which is the part a human can check |
| **D8** | Conversation context | **5 turns** | Enough for *"and what about above £500?"* to resolve. More starts dragging answers toward earlier topics |
| **D9** | Does a follow-up re-retrieve? | **yes, always** | REQ-C5. *"And above £500?"* needs a different row of the same table. Reusing the previous passages gives a confident answer from the wrong place, and it still looks right |

---

## What we build

| Order | Area | Files |
|---|---|---|
| 1 | **Ingest** F1 | `app/ingest/loader.py`, `chunker.py`, `pipeline.py`, `__main__.py` |
| 2 | **Retrieve + refuse** F2/F3 | `app/retrieve/service.py` |
| 3 | **Generate** F4 | `app/generate/service.py`, `prompts/answer.v1.md` |
| 4 | **API + persistence** F5/F6/F7 | `app/core/models.py`, `app/api/{ask,corpus,schemas}.py` |
| 5 | **Interface** F5/F6/F7 | `frontend/app/*`, `frontend/components/*` |

**Built in parallel** by four agents against fixed interfaces, because the
contracts between them are already written down in the PRD.

## Why this order

Ingest first because nothing can be tuned without an indexed corpus. Refusal before
generation because generation must be *unable* to run on an insufficient result — that
is a type, and types are easier to get right before there is a caller. The API last
because it is the only piece that needs all the others.

## What we will NOT do

- A settings page or a conversation list — PRD §11
- Streaming, authentication, re-ranking
- F8–F11

## The riskiest part

**Threshold tuning (D2).** Thirteen questions is a small evaluation set, and a value that
separates them may not generalise. **If it fails:** prefer refusing slightly too often —
a refusal is recoverable, a confident invention is not.

---

## Approval

| | |
|---|---|
| **Decision** | APPROVED |
| **By** | Release manager — decisions delegated |
| **When** | 25 September 2026 |
