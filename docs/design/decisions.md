# Decisions — PRD §10

Recorded from the decision interview, 2026-09-27. Choices and reasons are the team's,
in the team's words. Anything still open is marked **Open**.

| # | Decision | Chosen | Reason given |
|---|---|---|---|
| **D0** | Embedding model and dimensions | `text-embedding-3-small`, 1536 | Verified working. 3072 doubles cost and storage for a five-document corpus that is not hard to search. Re-indexing later is one command. |
| **D1** | Chunk size and overlap | Section-first, `CHUNK_MAX_TOKENS=400`, `CHUNK_OVERLAP_TOKENS=60`. Only a section over 400 splits, on paragraph boundaries | Policy is already written in numbered sections, and a citation to "4.2 Approval thresholds" is something a human can verify. |
| **D2** | Refusal threshold | `MIN_SCORE=0.35`, tuned against `EVALUATION.md`. Set below the lowest true answerable score rather than midway to the refusals | The model is a second line of defence — it declines when passages do not answer. A threshold set to catch everything refuses valid rephrasings. |
| **D3** | Passages retrieved | `RETRIEVE_TOP_K=6` | Enough for an answer spanning two sections; few enough that the weakest is still relevant. |
| **D4** | Superseded policies | Shown, flagged loudly | The corpus indexes them so "has this changed?" is answerable. An answer citing a withdrawn policy is the failure we exist to prevent, so it has to be impossible to miss. |
| **D5** | What a refusal says | Say what is not covered, and name the owning team | "I don't know" leaves the user where they started. Every document names an owner in its front matter. |
| **D6** | Conflicting policies | Surface both, name the conflict, do not resolve it | The retention/outsourcing conflict is a governance problem Aldermere already has. Resolving it in code makes our software decide which policy wins. |
| **D7** | Citation grouping | One citation per section, deduplicated, highest score wins | Grouping by document would lose the section, which is the part a human can check. |
| **D8** | Conversation a follow-up sees | `CONTEXT_MESSAGES=5` *(F6 — outside T1)* | Enough for "and what about above 500?" to resolve; more starts dragging answers toward earlier topics. |
| **D9** | Follow-up re-retrieval | Yes, every turn — on the conversation (earlier user turns + the new question), not the fragment *(F6 — outside T1)* | "And above 500?" needs a different row of the same table, so reusing the previous passages answers confidently from the wrong section. But embedded alone that fragment matches nothing, so the query carries the earlier user turns. |

## Notes

**D1 — overlap vs REQ-I2.** The 60-token overlap must be taken in whole sentences, or
the second half of a split section starts mid-sentence. No section in the current corpus
exceeds 400 tokens, so the split path is untested by real data.

**D2 — condition (team chose option a).** 0.35 is a starting value, not a tuned one:
nothing was indexed when it was chosen. In stage 03 it must refuse all three
out-of-scope questions (REQ-R6) **on the threshold alone** — the model is not relied on
to decline. If Q11–Q13 score above it, the number moves. The thirteen scores are recorded
below, since `EVALUATION.md` is protected.

**D5 — detail (team chose option a).** A refusal lists the four policy areas and their
owning teams, read from each document's front matter, and points to Compliance for
anything outside them. No model call. A question no document owns (Q12, Q13) is never
routed to the nearest document's owner.

## D2 — evaluation scores

Live index, 130 passages, `text-embedding-3-small`, `RETRIEVE_TOP_K=6`, 2026-09-27.
Outcome is at `MIN_SCORE=0.35`. Produced by `python -m tests.eval.evaluation`.

| Q | Question | Top score | Expected section in top 3? | Outcome at 0.35 |
|---|---|---|---|---|
| 1 | approval threshold | 0.831 | yes — rank 2 (rank 1 is superseded v3.0 §4.1) | grounded |
| 2 | exactly £75 | 0.659 | yes — rank 1 | grounded |
| 3 | business class | **0.526** | yes — rank 1 | grounded |
| 4 | Singapore cap | 0.611 | yes — rank 1 | grounded |
| 5 | high-risk refresh | 0.731 | yes — rank 2 | grounded |
| 6 | 90 days overdue | 0.743 | yes — rank 1 | grounded |
| 7 | EDD ownership % | 0.535 | yes — rank 1 | grounded |
| 8 | correspondence retention | 0.750 | yes — ranks 2 (§4.1), 1 (§4.2) | grounded |
| 9 | critical outsourcing approval | 0.691 | yes — rank 1 | grounded |
| 10 | the conflict | 0.621 | yes — both: §6.4 rank 2, §4.1 rank 3 | grounded |
| 11 | partner's flight | **0.510** | must refuse | **grounded — FAILS** |
| 12 | cryptocurrency | 0.491 | must refuse | **grounded — FAILS** |
| 13 | parental leave | 0.257 | must refuse | insufficient |

**Lowest answerable top score: 0.526 (Q3). Highest out-of-scope: 0.510 (Q11). Gap: 0.016.**
0.35 does not meet the D2 condition. **Awaiting the team's decision.**
