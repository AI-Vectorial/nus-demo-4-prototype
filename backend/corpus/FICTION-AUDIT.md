# Fiction audit

**Every document in this corpus is invented. Aldermere Bank does not exist.**

This records what was checked, by what method, and what was found — so that the
claim is evidenced rather than asserted.

| | |
|---|---|
| **Documents audited** | 5 |
| **Date** | 26 September 2026 |
| **Method** | Automated entity scan + per-document read |
| **Result** | **PASS** — no real-world organisation appears |

---

## What was scanned for

An automated scan over all five documents, matching whole words, case-insensitive:

| Category | Terms |
|---|---|
| **Banks** | MUFG · Mitsubishi · HSBC · Barclays · Lloyds · NatWest · Santander · Citibank · JPMorgan · Goldman · Morgan Stanley · Deutsche · UBS · Credit Suisse · BNP · Standard Chartered · DBS · OCBC · UOB · Nomura · Mizuho |
| **Regulators** | FCA · PRA · MAS · SEC · FINRA · BaFin · JFSA · OCC · FDIC |
| **Vendors** | Salesforce · Workday · SAP · Oracle · Concur · Coupa · Fiserv · Temenos · Murex |
| **Common surnames** | Smith · Patel · Tanaka · Chen · Kumar · Wong |

**Result: 0 matches across all five documents.**

---

## Per-document sign-off

| Document | Entities | Figures | People | Verdict |
|---|---|---|---|---|
| Travel and Expense Policy v3.1 | none real | invented | none named | ✅ |
| Travel and Expense Policy v3.0 | none real | invented | none named | ✅ |
| Client Onboarding and KYC Refresh v2.4 | none real | invented | none named | ✅ |
| Records Retention and Data Handling v4.0 | none real | invented | none named | ✅ |
| Outsourcing and Third-Party Risk v1.8 | none real | invented | none named | ✅ |

**Internal bodies named** — all invented, all internal to Aldermere: Group Finance ·
Financial Crime Compliance · Group Legal and Company Secretariat · Group Operational
Risk · Policy Office · Outsourcing Committee · Audit Committee · Employee Relations ·
Board Remuneration Framework.

**No individual is named anywhere.** Roles only — line manager, Department Head,
relationship manager, regional head.

---

## What is referenced but is not an organisation

`EEA` · `Hong Kong` · `London` · `New York` · `Singapore` · `Tokyo` · `United Kingdom`

Geographies and one trade bloc. **No claim is made about any real jurisdiction's law.**
Where the documents mention regulation they do so generically — *"applicable
anti-money-laundering regulation"*, *"a regulator"*, *"local law"* — and never cite a
statute, a rule number or a named authority.

> **This was deliberate.** A fictional bank with invented policies is safe. A fictional
> bank citing a real rule number is a statement about real regulation that happens to be
> wrong.

---

## Findability check

*Can a reader holding the whole corpus answer the evaluation questions? If not, it is a
corpus defect, and no amount of retrieval tuning fixes it.*

All thirteen questions from `EVALUATION.md` were put to a reader given the complete
document set and no retrieval.

**Result: 12 of 13 as expected.**

| | |
|---|---|
| Q1–Q10 findable | ✅ 10/10, each citing the expected section |
| Q12, Q13 absent | ✅ both returned "not in the corpus" |
| **Q11 — partner's flight** | ⚠️ **see below** |

### ⚠️ Q11 is not a clean absence

Asked *"Can I expense my partner's flight?"*, a reader with the whole corpus answered:

> *"No — the policy only allows reimbursement for expenses necessary for business
> purposes."*

That is **§2.1 Necessity**, and it is a fair inference. The corpus does not *state* a
rule about partners; a careful reader can *derive* a likely answer from a general
principle.

**This is being kept, not fixed, and the distinction is the point.**

| | |
|---|---|
| **A human reasoning from a principle** | legitimate, and what §2.1 is for |
| **An assistant doing the same** | the failure this product exists to prevent |

The policy does not say. An assistant that answers anyway has inferred a rule that
Aldermere has not written — and would say it with the same confidence as a real one.

**The deployed build refuses Q11**, which is the behaviour we want. But the question is
now recorded as *"inferable, not stated"* rather than *"absent"*, because claiming a
clean absence would be untrue.

---

## What this audit does not cover

**A human cold read.** Three readers who did not write the corpus, answering the thirteen
questions from the documents alone and recording how long each took. The check above is
machine-assisted and tests **findability**, not **readability** — whether a person can
locate an answer under time pressure is a different question, and it needs people.

| Reader | Date | Q1–10 | Q11–13 correctly unanswerable | Notes |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |

---

*Aldermere Bank is fictional · This corpus is a teaching artefact*
