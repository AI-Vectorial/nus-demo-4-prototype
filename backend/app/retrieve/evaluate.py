"""The evaluation set, run against the live index. REQ-R5, REQ-R6.

    python -m app.retrieve.evaluate

Transcribed from corpus/EVALUATION.md. Each requirement is a list of
alternatives; a requirement is met when any alternative is in the top three.
An alternative is (document id, version, section heading prefix). Versions are
named so a superseded v3.0 section can never satisfy a question about v3.1.

Prints the top score for every question, Q1-Q13. Those scores are the input to
the refusal threshold (D2). This module does not decide refusal; F3 does.
"""

from __future__ import annotations

from app.retrieve.search import retrieve
from app.retrieve.store import Hit

TOP_CHECK = 3

TRAVEL = "travel-expense-policy"
KYC = "client-onboarding-kyc"
RETENTION = "records-retention"
OUTSOURCING = "outsourcing-third-party"

Alternative = tuple[str, str, str]
Requirement = list[Alternative]

# Q1-Q10: the corpus supports these. Each entry: (question, requirements).
ANSWERABLE: list[tuple[str, list[Requirement]]] = [
    ("What is the approval threshold for a travel expense claim?",
     [[(TRAVEL, "3.1", "4.2 Approval thresholds")]]),
    ("Does a claim of exactly £75 need approval?",
     [[(TRAVEL, "3.1", "4.2 Approval thresholds")]]),
    ("Can I fly business class on a six-hour flight?",
     [[(TRAVEL, "3.1", "5.2 Air travel")]]),
    ("What is the accommodation cap for a night in Singapore?",
     [[(TRAVEL, "3.1", "6.2 Accommodation caps")]]),
    ("How often do we refresh KYC for a high-risk client?",
     [[(KYC, "2.4", "6.1 Refresh cycles")]]),
    ("What happens if a KYC refresh is more than 90 days overdue?",
     [[(KYC, "2.4", "6.4 Overdue refresh")]]),
    ("At what ownership percentage do we identify beneficial owners under enhanced due diligence?",
     [[(KYC, "2.4", "4.2 Enhanced due diligence")]]),
    ("How long do we keep client correspondence?",
     [[(RETENTION, "4.0", "4.1 General table"), (RETENTION, "4.0", "4.2 Client correspondence")]]),
    ("Who can approve a critical outsourcing arrangement?",
     [[(OUTSOURCING, "1.8", "4.1 Approval authority")]]),
    ("A provider holds our client correspondence. How long can they keep it after we terminate?",
     [[(OUTSOURCING, "1.8", "6.4 Return and destruction")],
      [(RETENTION, "4.0", "4.1 General table"), (RETENTION, "4.0", "4.2 Client correspondence")]]),
]

# Q11-Q13: the corpus does not support these. Refusal is checked in F3.
UNANSWERABLE: list[str] = [
    "Can I expense my partner's flight if they travel with me?",
    "What is our policy on cryptocurrency held by clients?",
    "How many days of paid parental leave am I entitled to?",
]


def matches(hit: Hit, alternative: Alternative) -> bool:
    document_id, version, prefix = alternative
    return (
        hit.document_id == document_id
        and hit.metadata.get("version") == version
        and hit.section.startswith(prefix)
    )


def satisfied(hits: list[Hit], requirements: list[Requirement]) -> bool:
    """Every requirement has an alternative in the top TOP_CHECK hits."""
    top = hits[:TOP_CHECK]
    return all(
        any(matches(hit, alternative) for hit in top for alternative in requirement)
        for requirement in requirements
    )


def _show_top(hits: list[Hit]) -> None:
    for rank, hit in enumerate(hits[:TOP_CHECK], start=1):
        version = hit.metadata.get("version")
        print(f"      {rank}. {hit.score:.4f}  {hit.document_id} v{version}  {hit.section}")


def main() -> int:
    from app.generate import embed
    from app.retrieve import get_vector_store

    store = get_vector_store()
    passed = 0
    for number, (question, requirements) in enumerate(ANSWERABLE, start=1):
        hits = retrieve(question, store, embed)
        ok = satisfied(hits, requirements)
        passed += ok
        verdict = "PASS" if ok else "FAIL"
        print(f"Q{number:<2} {verdict}  top={hits[0].score:.4f}  {question}")
        _show_top(hits)

    print(f"\nanswerable: {passed}/{len(ANSWERABLE)} pass")
    for number, question in enumerate(UNANSWERABLE, start=11):
        hits = retrieve(question, store, embed)
        print(f"Q{number} top={hits[0].score:.4f}  {question}")
        _show_top(hits)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
