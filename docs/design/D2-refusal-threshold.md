# D2 — The refusal threshold

**Decided:** 2026-10-08, table 3, stage 02 decision interview
**Status:** locked · **`MIN_SCORE=0.485` signed off by the project owner / requester, 2026-10-08 06:58 UTC**

## What we chose

**Method** (wording corrected by the team on 2026-10-08, stage 03, see below).

> If the answerable and unanswerable score distributions have a clear gap, set
> `MIN_SCORE` within that gap, using the midpoint as the default. If the distributions
> overlap, do not force a threshold to satisfy all evaluation questions. Prefer the
> threshold that minimises unsupported answers, even if that causes some answerable
> evaluation questions to be refused, and report the resulting trade-off for sign-off.

The conservative threshold is **above the strongest clearly unsupported cases**, not below
the weakest answerable case. Whether a gap is "clear" is judged by the team at sign-off.

*Correction.* As first recorded, the overlap option read "just below the lowest answerable
score". That leans towards **answering**, the opposite of the team's intent. The agent
framed it wrongly at the interview, and the first measurement exposed it. The team gave
the wording above.

**How it is applied.** Per passage. Every retrieved passage below `MIN_SCORE` is
discarded (REQ-R2). If none survive, we refuse.

**What it is measured on.** Standalone questions **and** the combined text a follow-up
retrieves on (D9), including Q11 asked as a follow-up to Q1.

## Why

The product's stated priority is avoiding confident wrong answers. When the
distributions overlap, B is better than C, which would lean towards answering.

## Consequences

- Determines C4, C5, C7 and refusal behaviour.
- Tuned only after D1, D3, D4, D6 and D9 are in place.
- The scaffold's fallback `MIN_SCORE=0.35` (`backend/app/core/config.py`) is not a
  decision. It must be replaced explicitly by the signed-off value.

## Measured value

**Status: no value chosen. The scores do not separate, so the build stopped for the team's
review (stage 03, 2026-10-08).**

`python -m app.retrieve.evaluate`, D0 `text-embedding-3-small` 1536, D1 one passage per
section with title + heading prefixed, D3 top-k 5, no threshold applied.
"Score" is the expected section's score for answerable rows (it must survive the
threshold), and the top score of any passage for rows that must refuse.

| | Q | Score | Expected section rank | Must |
|---|---|---|---|---|
| 1 | approval threshold | 0.802 | 2 (v3.0 §4.1 is 1st at 0.829) | answer |
| 2 | exactly £75 | 0.653 | 1 | answer |
| 3 | business class | **0.494** | 1 | answer |
| 4 | Singapore cap | 0.598 | 1 | answer |
| 5 | high-risk refresh | 0.753 | 1 | answer |
| 6 | 90 days overdue | 0.758 | 1 | answer |
| 7 | EDD ownership % | 0.535 | 1 | answer |
| 8 | correspondence retention | 0.754 | 1 (§4.2) | answer |
| 9 | critical outsourcing approval | 0.690 | 1 | answer |
| 10 | the conflict | 0.520 | 2 and 3 (§6.4 0.521, §4.1 0.520) | answer |
| C14 | follow-up "above that limit" | 0.707 | 2 | answer |
| 11 | partner's flight | **0.517** | — (top: v3.1 §5.2 Air travel) | refuse |
| 12 | cryptocurrency | **0.494** | — (top: KYC §9 Related policies) | refuse |
| 13 | parental leave | 0.264 | — | refuse |
| C31 | Q1 then Q11 | **0.732** | — (top: v3.0 §4.1 Approval thresholds) | refuse |

- Lowest expected-section score: **0.494** (Q3). Highest score that must refuse:
  **0.517** standalone (Q11), **0.732** with C31.
- Gap: **−0.023** on the 13 questions alone, **−0.239** with C31. No threshold passes all
  thirteen, and none comes close to passing C31.
- Every expected section is in the top three (C4's retrieval half holds).
- Searched alone, the C14 follow-up scores 0.495 and Q11 scores 0.517, so gating on the
  current question by itself would not separate them either.

## Experiments 3a and 3b (measurement only, 2026-10-08)

Authorised by the team as **measurement only**. Each was indexed into a `scratch_*`
collection in the local Qdrant. **Nothing was changed in the product.** D0 and D1 stand as
decided until the team says otherwise.

| | small + prefix *(current D0/D1)* | 3a: small, no prefix | 3b: large + prefix | 3a+3b: large, no prefix |
|---|---|---|---|---|
| Q1 | 0.802 r2 | 0.720 r1 | 0.731 r2 | 0.710 r1 |
| Q2 | 0.653 r1 | 0.732 r1 | 0.695 r1 | 0.722 r1 |
| Q3 | **0.494** r1 | 0.613 r2 | **0.524** r1 | 0.565 r1 |
| Q4 | 0.598 r1 | 0.621 r1 | 0.592 r2 | 0.638 r1 |
| Q5 | 0.753 r1 | **0.507 r5 ✗** | 0.773 r1 | 0.599 r1 |
| Q6 | 0.758 r1 | 0.600 r1 | 0.732 r1 | 0.642 r1 |
| Q7 | 0.535 r1 | 0.554 r1 | 0.604 r1 | **0.522** r1 |
| Q8 | 0.754 r1 | 0.708 r1 | 0.752 r1 | 0.743 r1 |
| Q9 | 0.690 r1 | 0.590 r2 | 0.694 r1 | 0.690 r1 |
| Q10 (weaker of the two) | 0.520 r3 | **0.552 r4 ✗** | 0.539 r3 | 0.577 r3 |
| C14 follow-up | 0.707 r2 | 0.573 r2 | 0.622 r2 | 0.582 r2 |
| Q11 | **0.517** | 0.454 | **0.446** | 0.423 |
| Q12 | 0.494 | 0.492 | 0.435 | **0.431** |
| Q13 | 0.264 | 0.252 | 0.241 | 0.253 |
| **C31** (Q1 then Q11) | **0.732** | 0.604 | 0.645 | 0.595 |
| **Gap, 13 questions + C14** | **−0.023** | +0.015 | **+0.078** | **+0.091** |
| Expected section outside top 3 | none | **Q5, Q10** | none | none |
| **Gap including C31** | −0.238 | −0.097 | −0.121 | −0.073 |

*rN = rank of the expected section. Answerable rows show the expected section's score;
refuse rows show the top score of any passage.*

**What it shows**

- **3a on its own fails C4.** Dropping the prefix moves Q5 to rank 5 and Q10's second
  section to rank 4.
- **3b separates the thirteen questions.** `text-embedding-3-large` gives a positive gap
  with every expected section in the top three: +0.078 with the prefix (Q3 0.524 against
  Q11 0.446, midpoint ≈ 0.485), and +0.091 without it (Q7 0.522 against Q12 0.431,
  midpoint ≈ 0.477). This is the evidence D0 said would justify revisiting the model.
- **C31 fails in every configuration.** Q1 then Q11 scores 0.595–0.732, above several
  answerable questions every time. No threshold, on either model, passes C31 under the
  approved D9.
- **Searching the current question alone doesn't separate them either** (large model):
  C14's follow-up alone scores 0.419–0.427 and Q11 alone 0.423–0.446.

**No product change has been made.** Whether to adopt 3b (a D0 change with a re-index)
and what to do about C31 and D9 are open decisions for the team.

## Real index after the D0 revision (2026-10-08)

`text-embedding-3-large`, 3072, D1 prefix kept. Re-indexed with `--force`: 135 passages,
ids unchanged. `python -m app.retrieve.evaluate`:

| | Q | Score | Expected section rank | Must |
|---|---|---|---|---|
| 1 | approval threshold | 0.731 | 2 (v3.0 §4.1 1st at 0.757) | answer |
| 2 | exactly £75 | 0.695 | 1 | answer |
| 3 | business class | **0.524** | 1 | answer |
| 4 | Singapore cap | 0.592 | 2 (v3.0 §6.1 1st at 0.594) | answer |
| 5 | high-risk refresh | 0.773 | 1 | answer |
| 6 | 90 days overdue | 0.732 | 1 | answer |
| 7 | EDD ownership % | 0.605 | 1 | answer |
| 8 | correspondence retention | 0.752 | 1 | answer |
| 9 | critical outsourcing approval | 0.694 | 1 | answer |
| 10 | the conflict | 0.539 | §4.1 2nd (0.570), §6.4 3rd (0.539) | answer |
| C14 | follow-up | 0.622 | 2 | answer |
| 11 | partner's flight | **0.446** | — | refuse |
| 12 | cryptocurrency | 0.435 | — | refuse |
| 13 | parental leave | 0.241 | — | refuse |
| C31 | Q1 then Q11 | **0.645** | — | refuse |

The experiment reproduces exactly.

- **The 13 questions and C14:** lowest that must pass 0.524 (Q3), highest that must refuse
  0.446 (Q11). **Gap +0.078.** Every expected section is in the top three.
- **Proposed `MIN_SCORE` = 0.485**, the midpoint, by the method above. Margins: 0.039 to
  Q3 and 0.039 to Q11.
- **Status: PROPOSED, awaiting the team's sign-off.** It is not in configuration.
- **C31 (0.645) is above the proposal and above five answerable questions.** No threshold
  passes it. It stays a failing criterion for the release gate (see T1).
- The superseded version outranks the current one for Q1 and Q4. D4 relies on the
  labelling and the prompt to make the current version govern.

## Sign-off

| | |
|---|---|
| **Value** | `MIN_SCORE=0.485` |
| **Signed off by** | Project owner / requester |
| **When** | 2026-10-08 06:58 UTC |
| **Basis** | Midpoint of the +0.078 gap on the real `text-embedding-3-large` + prefix index (Q3 0.524, Q11 0.446), by the method above |
| **Known limitation** | C31 (Q11 after Q1, 0.645) is not separated by this or any threshold. It goes to the release gate as a failing criterion, with D9 and C31 unchanged by the team's decision |

Set as the decided value in `backend/app/core/config.py` and `backend/.env.example`.
