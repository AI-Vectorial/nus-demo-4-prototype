"""Run the thirteen questions in corpus/EVALUATION.md against the live index.

    python -m app.retrieve.evaluate

Prints the score table EVALUATION.md asks for, and the gap D2 is chosen from.
Exits non-zero if, at the configured MIN_SCORE, an answerable question misses
its section in the top three or refuses, or an out-of-scope one does not refuse.

The expected sections are copied from EVALUATION.md, which is protected. If it
changes, this list must change with it.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from app.core.config import settings
from app.generate import embed
from app.retrieve import Grounded, get_vector_store, retrieve

TOP = 3

# Cosine similarity's floor: every passage passes, so every score is visible.
UNTHRESHOLDED = -1.0


@dataclass(frozen=True)
class Case:
    number: int
    question: str
    # Any one of these (document_id, version, section number) in the top three
    # passes. Empty means the corpus cannot answer and the question must refuse.
    expected: tuple[tuple[str, str, str], ...]
    # For the conflict question: every one of these should be retrieved (D6).
    all_of: tuple[tuple[str, str, str], ...] = ()


TRAVEL = ("travel-expense-policy", "3.1")
KYC = ("client-onboarding-kyc", "2.4")
RETENTION = ("records-retention", "4.0")
OUTSOURCING = ("outsourcing-third-party", "1.8")

CASES = [
    Case(1, "What is the approval threshold for a travel expense claim?", ((*TRAVEL, "4.2"),)),
    Case(2, "Does a claim of exactly £75 need approval?", ((*TRAVEL, "4.2"),)),
    Case(3, "Can I fly business class on a six-hour flight?", ((*TRAVEL, "5.2"),)),
    Case(4, "What is the accommodation cap for a night in Singapore?", ((*TRAVEL, "6.2"),)),
    Case(5, "How often do we refresh KYC for a high-risk client?", ((*KYC, "6.1"),)),
    Case(6, "What happens if a KYC refresh is more than 90 days overdue?", ((*KYC, "6.4"),)),
    Case(7, "At what ownership percentage do we identify beneficial owners under enhanced "
            "due diligence?", ((*KYC, "4.2"),)),
    Case(8, "How long do we keep client correspondence?",
         ((*RETENTION, "4.1"), (*RETENTION, "4.2"))),
    Case(9, "Who can approve a critical outsourcing arrangement?", ((*OUTSOURCING, "4.1"),)),
    Case(10, "A provider holds our client correspondence. How long can they keep it after we "
             "terminate?", ((*OUTSOURCING, "6.4"), (*RETENTION, "4.1")),
         all_of=((*OUTSOURCING, "6.4"), (*RETENTION, "4.1"))),
    Case(11, "Can I expense my partner's flight if they travel with me?", ()),
    Case(12, "What is our policy on cryptocurrency held by clients?", ()),
    Case(13, "How many days of paid parental leave am I entitled to?", ()),
]


def _key(hit) -> tuple[str, str, str]:
    return hit.document_id, str(hit.metadata.get("version")), hit.section.split(" ", 1)[0]


def _rank(hits, wanted) -> int | None:
    for index, hit in enumerate(hits, start=1):
        if _key(hit) in wanted:
            return index
    return None


def main() -> int:
    store = get_vector_store()
    failures: list[str] = []
    answerable_tops: list[float] = []
    refusal_tops: list[float] = []

    print(f"MIN_SCORE={settings.min_score}  RETRIEVE_TOP_K={settings.retrieve_top_k}  "
          f"{settings.embedding_model_slug}\n")
    print(f"{'Q':>3}  {'top':>6}  {'rank':>4}  {'outcome':<12}  top hit")
    for case in CASES:
        # Unthresholded, so every score is visible -- including the ones D2 discards.
        raw = retrieve(case.question, store, embed, min_score=UNTHRESHOLDED)
        hits = raw.hits if isinstance(raw, Grounded) else []
        top = hits[0].score if hits else 0.0
        outcome = retrieve(case.question, store, embed)
        refused = not isinstance(outcome, Grounded)

        rank = _rank(hits[:TOP], set(case.expected)) if case.expected else None
        if case.expected:
            answerable_tops.append(top)
            if rank is None:
                failures.append(f"Q{case.number}: expected section not in top {TOP}")
            if refused:
                failures.append(f"Q{case.number}: refused, but the corpus answers it")
            missing = [w for w in case.all_of if _rank(hits, {w}) is None]
            if missing:
                print(f"     Q{case.number} did not retrieve {missing} in top "
                      f"{settings.retrieve_top_k}")
        else:
            refusal_tops.append(top)
            if not refused:
                failures.append(f"Q{case.number}: answered, but must refuse")

        label = "refused" if refused else "grounded"
        first = f"{hits[0].document_id} v{hits[0].metadata.get('version')} {hits[0].section}"
        print(f"{case.number:>3}  {top:6.3f}  {rank or '-':>4}  {label:<12}  {first}")

    low, high = min(answerable_tops), max(refusal_tops)
    print(f"\nlowest answerable top score   {low:.3f}")
    print(f"highest out-of-scope top score {high:.3f}")
    if low > high:
        print(f"gap {high:.3f} .. {low:.3f}, midpoint {(low + high) / 2:.3f}")
    else:
        print("NO GAP: the two groups overlap")

    for failure in failures:
        print("FAIL", failure)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
