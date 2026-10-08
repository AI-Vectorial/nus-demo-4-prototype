# T1-F2 — Retrieve

**Parent:** [T1](T1.md)
**Feature:** F2 Retrieve
**Covers:** REQ-R1, REQ-R5
**Criteria:** C4 (retrieval half: the expected section in the top three)
**Status:** `done`

## Done when

Each of the ten answerable questions in `corpus/EVALUATION.md` returns its expected section in the top three results.

## Decisions this depends on

- **D3** — how many passages to retrieve.

## Notes

For Q10, the expected result is that both conflicting sections are retrieved. How the conflict is then presented is D6, under F4.

## Evidence

`python -m app.retrieve.evaluate`, 2026-10-08, against the live index (no threshold):
every expected section is in the top three. Q1–Q9 at rank 1 or 2. Q10: Outsourcing §6.4
at rank 2 and Records Retention §4.1 at rank 3. Full table in
`docs/design/D2-refusal-threshold.md`.

Whether those sections **survive** the threshold is D2, which is not yet set: see the
open question there. `tests/features/test_f2_retrieve.py`: 10 passed (REQ-R2, R3, D9
window).
