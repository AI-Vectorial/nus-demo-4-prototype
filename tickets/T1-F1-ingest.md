# T1-F1 — Ingest the corpus

**Parent:** [T1](T1.md)
**Feature:** F1 Ingest the corpus
**Covers:** REQ-I1 … REQ-I7
**Status:** `done`

## Done when

`python -m app.ingest` indexes the corpus, and running it twice changes nothing — same passage count, same ids.

## Decisions this depends on

- **D0** — `text-embedding-3-small`, 1536. Switching to 3072 means `--force` re-indexing; the collection is fixed at the first dimension used
- **D1** — section-first, 400 tokens max, 60 overlap, splitting only on paragraph boundaries. A smaller cap would split sections and make citations vaguer

## Evidence

Live Qdrant, table 3's collection, 2026-09-27. The id-set hash is a SHA-1 of every point id, sorted.

```
before:
points=130  id-set sha1=40b75b5ade26
by status: {('outsourcing-third-party', '1.8', 'current'): 28, ('records-retention', '4.0', 'current'): 26,
            ('travel-expense-policy', '3.0', 'superseded'): 19, ('client-onboarding-kyc', '2.4', 'current'): 26,
            ('travel-expense-policy', '3.1', 'current'): 31}
$ python -m app.ingest
indexed 130 passages from 5 documents in 3.0s -- collection now holds 130
points=130  id-set sha1=40b75b5ade26
$ python -m app.ingest --force
indexed 130 passages from 5 documents in 3.6s -- collection now holds 130
points=130  id-set sha1=40b75b5ade26
```

Same count, same ids, on a re-run and on `--force`. The superseded v3.0 is indexed with
`status: superseded` (REQ-I7). Under 60s (NFR-4).

```
$ pytest -q tests/features/test_ingest.py
16 passed
```

## Notes

- Passages are embedded as `<title> — <section>` + text; the stored `text` is the section body only
- No real section reaches 400 tokens (asserted by `test_no_real_section_exceeds_the_cap`), so the split path is exercised only by a synthetic document
- A single paragraph over the cap stays whole rather than breaking a sentence or table
