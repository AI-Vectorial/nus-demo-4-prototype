# T1-F3 — Refuse

**Parent:** [T1](T1.md)
**Feature:** F3 refuse
**Covers:** REQ-R2, REQ-R3, REQ-R4, REQ-R6
**Status:** `done`

## Done when

All three out-of-scope questions refuse with zero model calls, and all ten answerable
ones do not — epic criteria 8 – 12 pass.

## Decisions this depends on

- **D2** — the refusal threshold, and how it was arrived at. Too high and answerable questions refuse (criterion 7 fails); too low and out-of-scope ones get answered (criterion 9 fails)
- **D5** — what a refusal says. Decides the reason text in a `refused` response and where it points the user

## D2 — the threshold: `MIN_SCORE=0.517`

Measured 2026-09-30 with every score unthresholded (top five, `*` = expected section,
`sup` = superseded v3.0):

```
Q1   0.836 sup  0.810*    0.749      Q8   0.749*  0.589*  0.508
Q2   0.667*     0.626 sup 0.515      Q9   0.689   0.684*  0.645
Q3   0.533*     0.513 sup 0.451      Q10  0.618   0.576*  0.524*
Q4   0.622*     0.615 sup 0.421      ───── must refuse ─────
Q5   0.767      0.738*    0.696      Q11  0.501 sup 0.499  0.495
Q6   0.753*     0.718     0.659      Q12  0.490   0.459   0.454
Q7   0.553*     0.508     0.504      Q13  0.258   0.257   0.252
```

**Chosen:** 0.517 — the midpoint of the gap between the highest out-of-scope top score
(0.501, Q11) and the lowest answerable one (0.533, Q3), per the rule agreed in the plan.
Presented to the team with 0.51 and 0.525 as alternatives; team replied "go with your own
recommendation", was shown the recommendation and replied **"confirm"**.

**Why not 0.525:** Retention §4.1 scores 0.524 on Q10 — it would be discarded, and the
conflict answer would silently show one side only, defeating D6.

**Known limitation.** The gap is 0.032 wide, measured on thirteen questions. Q3 clears
by 0.016, Q11 refuses by 0.016, Q10's Retention §4.1 survives by 0.007. A rephrasing could
land on the wrong side. Re-measure whenever the embedding model, chunking or embedded text
changes. At the scaffold placeholder of 0.35, Q11 and Q12 were answered.

**Also observed:** on Q1 the superseded v3.0 section outscores the current v3.1 one
(0.836 vs 0.810) — which is why D4's "current version governs" prompt instruction matters.

## Evidence — 2026-09-30

At `MIN_SCORE=0.517`: Q11 – Q13 refuse, Q1 – Q10 are grounded (table in
[T1-F2](T1-F2-retrieve.md)). `pytest -q tests/features/test_f2_f3_retrieve_refuse.py`
covers criteria 8, 9, 10 and 12, including a fresh process with `MIN_SCORE=1.01` in which
all thirteen refuse.

**Criterion 11**, measured through the live local `/ask` in F5: five refusals of Q11 took
1.34 s (first, cold), 0.81, 0.53, 0.76, 0.72 s — all under 1.5 s. Also asserted in
`tests/features/test_f5_ask.py::test_a_refusal_is_fast`.
