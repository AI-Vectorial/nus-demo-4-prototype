# Evaluation set

**Thirteen questions. Ten the corpus answers, three it does not.**

This is the fixed evaluation set. **Tune your refusal threshold against it** — PRD
decision D2 asks how you arrived at your number, and *"it felt right"* is not an answer.

> ⚠️ **This file is protected.** If a question does not pass, fix retrieval. Do not edit
> the question and do not edit the corpus.

---

## How to use it

1. Index the corpus
2. Run all thirteen questions
3. For Q1–Q10, check the expected section appears in your top three results
4. For Q11–Q13, check your system **refuses**
5. Choose the threshold that separates them — and **record the score distribution**, so
   you can say why

If a threshold exists that passes all thirteen, you have a defensible number. If none
does, say so and explain which way you erred and why. **That is a better answer than a
number with no reasoning behind it.**

---

# Answerable — the corpus supports these

### Q1 — What is the approval threshold for a travel expense claim?
**Document:** Travel and Expense Policy v3.1
**Section:** 4.2 Approval thresholds
**Expected:** £75 or more requires line-manager approval.
**Note:** ⚠️ The superseded v3.0 says **£50**. Both are indexed. What your system does
about that is **decision D4**.

### Q2 — Does a claim of exactly £75 need approval?
**Document:** Travel and Expense Policy v3.1
**Section:** 4.2 Approval thresholds
**Expected:** Yes. The policy states thresholds are inclusive and that a claim of exactly
£75 requires line-manager approval.
**Note:** The boundary. An implementation using `>` instead of `>=` gets this wrong while
passing every other question.

### Q3 — Can I fly business class on a six-hour flight?
**Document:** Travel and Expense Policy v3.1
**Section:** 5.2 Air travel
**Expected:** No. Four to eight hours is economy; premium economy with Department Head
approval. Business class is for flights over eight hours.

### Q4 — What is the accommodation cap for a night in Singapore?
**Document:** Travel and Expense Policy v3.1
**Section:** 6.2 Accommodation caps
**Expected:** £300 per night, inclusive of taxes and service charges.

### Q5 — How often do we refresh KYC for a high-risk client?
**Document:** Client Onboarding and KYC Refresh Policy v2.4
**Section:** 6.1 Refresh cycles
**Expected:** Every 12 months, running from completion of the previous review.

### Q6 — What happens if a KYC refresh is more than 90 days overdue?
**Document:** Client Onboarding and KYC Refresh Policy v2.4
**Section:** 6.4 Overdue refresh
**Expected:** The relationship is suspended pending completion. Only Financial Crime
Compliance can lift the suspension.

### Q7 — At what ownership percentage do we identify beneficial owners under enhanced due diligence?
**Document:** Client Onboarding and KYC Refresh Policy v2.4
**Section:** 4.2 Enhanced due diligence
**Expected:** 10% or more, against 25% for standard due diligence.

### Q8 — How long do we keep client correspondence?
**Document:** Records Retention and Data Handling Policy v4.0
**Section:** 4.1 General table / 4.2 Client correspondence
**Expected:** Seven years from the **end of the client relationship**, not from the date
of the communication.

### Q9 — Who can approve a critical outsourcing arrangement?
**Document:** Outsourcing and Third-Party Risk Policy v1.8
**Section:** 4.1 Approval authority
**Expected:** Department Head, Group Operational Risk, Group Legal **and** the Outsourcing
Committee — all four.

### Q10 — ⭐ A provider holds our client correspondence. How long can they keep it after we terminate?
**Documents:** Outsourcing v1.8 §6.4 **and** Records Retention v4.0 §4.1
**Expected:** **This is the conflict.** Outsourcing requires destruction within five years
of termination. Records Retention requires seven years from the end of the relationship.
Both are current.

The corpus does not resolve it — Outsourcing §6.4 says to escalate to Group Legal and
Group Operational Risk jointly and **not to resolve it locally**.

> **What your system does here is decision D6, and it is the most interesting question in
> the set.** Surfacing both and naming the conflict is a good answer. Silently picking one
> is your software deciding which policy wins — which may be exactly the wrong thing for
> it to do.

---

# Not answerable — the corpus does not support these

**These must refuse.** A confident answer to any of them is the failure the product exists
to prevent.

### Q11 — Can I expense my partner's flight if they travel with me?
**Why it refuses:** The Travel and Expense Policy is silent on family members, partners
and dependants. Nothing in the corpus *states* a rule.
**A good refusal says:** the policy set does not cover this, and points at Group Finance.

> ⚠️ **This one is inferable, not absent — and that is the point.** Given the whole
> corpus, a careful reader answers *"no, because §2.1 only allows expenses necessary for
> business"*. That is a fair inference for a human and the wrong move for an assistant:
> the policy does not say, and an assistant that reasons to a rule Aldermere has not
> written will state it as confidently as a real one.
>
> Recorded in `FICTION-AUDIT.md` rather than fixed.

### Q12 — What is our policy on cryptocurrency held by clients?
**Why it refuses:** No document in the corpus addresses digital assets. Adjacent material
on client due diligence exists and may score moderately — **this is the question most
likely to produce a plausible invention.**

### Q13 — How many days of paid parental leave am I entitled to?
**Why it refuses:** Entirely outside the corpus. Four bank policies covering expenses,
onboarding, retention and outsourcing say nothing about employment benefits.

---

# Recording your results

Fill this in during stage 03 and cite it in your plan when defending **D2**.

| | Q | Top score | Expected section in top 3? | Outcome |
|---|---|---|---|---|
| 1 | approval threshold | | | |
| 2 | exactly £75 | | | |
| 3 | business class | | | |
| 4 | Singapore cap | | | |
| 5 | high-risk refresh | | | |
| 6 | 90 days overdue | | | |
| 7 | EDD ownership % | | | |
| 8 | correspondence retention | | | |
| 9 | critical outsourcing approval | | | |
| 10 | the conflict | | | |
| 11 | partner's flight | | **must refuse** | |
| 12 | cryptocurrency | | **must refuse** | |
| 13 | parental leave | | **must refuse** | |

**Chosen threshold:**
**Why:**

---

## Cold read — to be completed before the lab

*Ticket 08. Readers who did not write the corpus answer all thirteen using only the
corpus. A question two of three cannot answer is a corpus defect, not a retrieval one.*

| Reader | Date | Q1–10 correct | Q11–13 correctly unanswerable | Notes |
|---|---|---|---|---|
| | | | | |

---

*Aldermere Bank corpus · Evaluation set v1.0 · PROTECTED · This corpus is fictional.*
