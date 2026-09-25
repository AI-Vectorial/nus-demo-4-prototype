# 0001 — The refusal threshold, and why it is not the only defence

**Status:** accepted · **Date:** 26 September 2026 · Decisions **D2**, and the
`CANNOT_ANSWER` path

## Context

`MIN_SCORE` decides whether retrieval is good enough to answer from. Tuned once
against the thirteen questions in `corpus/EVALUATION.md`, it separated them
cleanly — answerable **0.55–0.73**, out-of-scope **0.45–0.48**.

Seven hundredths of separation. Real questions landed inside it:

| Question | Result |
|---|---|
| *"What is the **limit** for an evening meal?"* | answered — £40 |
| *"What is the **cap** for an evening meal?"* | **refused** |

One word, and the corpus answers both. §6.3 says *limits*; only accommodation
says *caps*.

## What we changed, and what it cost

Embedding was carrying the body text alone. §6.3 reads *"Meals are reimbursable
on days involving business travel…"* — the words **Travel**, **Expense** and
**Subsistence** appear nowhere in its vector, because they live in the headings.

So the vector now carries `<document title> - <section>` as a prefix. The
**stored** text is untouched; only what is matched against changed.

⚠️ **That invalidated the tuned threshold immediately.** Prefixing the passage
but not the query shifted every score down, and at `MIN_SCORE=0.52` questions
that had worked began refusing. **A threshold is tuned against an embedding
strategy, not against a corpus.** Change one and the other is stale.

## The finding that mattered more

Re-measured at `MIN_SCORE=0.05` — low enough that almost anything passes — the
three out-of-scope questions still returned **no citations at all**.

They were never caught by the threshold. **The model declined them**, returning
`CANNOT_ANSWER`, which the service turns into a refusal.

There are two lines of defence, not one:

| | Catches | Cost |
|---|---|---|
| **The threshold** | obviously irrelevant questions | none — no model call, refusal under 1.5s |
| **`CANNOT_ANSWER`** | questions that retrieve plausible passages that do not answer them | one model call |

## Decision

**`MIN_SCORE = 0.35`**, with the distribution measured after the embedding
change: answerable **0.44–0.83**.

Set below the lowest true answerable score rather than midway to the refusals,
because the model is the second line. A threshold set to catch everything
refuses valid rephrasings; one set to catch the obvious, backed by a model that
declines, does neither.

**15/15** on the evaluation set plus the two rephrasings that previously failed.

## Consequences

- An out-of-scope question now usually costs one model call. **NFR-2's sub-1.5s
  refusal holds only for the obvious ones.** Accepted: a false refusal is worse
  than a slow one.
- The threshold is coupled to `EMBEDDING_MODEL_SLUG` **and** to what ingestion
  embeds. Re-tune on either change; `scripts/tune_threshold.py` prints the
  distribution.
- `CANNOT_ANSWER` is a prompt contract. A model that ignores it puts us back on
  the threshold alone — worth re-checking whenever `LLM_MODEL` changes.
- Thirteen questions is a small set and this is tuned, not proven.

---

*Reference build · Aldermere Bank is fictional*
