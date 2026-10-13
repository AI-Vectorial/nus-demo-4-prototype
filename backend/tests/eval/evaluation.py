"""The fixed evaluation set, corpus/EVALUATION.md, against the live index.

Questions are copied verbatim from EVALUATION.md, which is protected. Run it to
print the score table D2 is defended with:

    python -m tests.eval.evaluation
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.generate import embed
from app.retrieve import get_vector_store
from app.retrieve.retrieve import search
from app.retrieve.store import Hit

# (document_id, version, section number) -- any one of a tuple's entries counts,
# except Q10, where BOTH sides of the conflict must be found.
TRAVEL = ("travel-expense-policy", "3.1")
KYC = ("client-onboarding-kyc", "2.4")
RETENTION = ("records-retention", "4.0")
OUTSOURCING = ("outsourcing-third-party", "1.8")


@dataclass(frozen=True)
class Question:
    number: int
    text: str
    expected: tuple[tuple[str, str, str], ...] = ()
    needs_all: bool = False

    @property
    def answerable(self) -> bool:
        return bool(self.expected)


QUESTIONS = [
    Question(1, "What is the approval threshold for a travel expense claim?", ((*TRAVEL, "4.2"),)),
    Question(2, "Does a claim of exactly £75 need approval?", ((*TRAVEL, "4.2"),)),
    Question(3, "Can I fly business class on a six-hour flight?", ((*TRAVEL, "5.2"),)),
    Question(4, "What is the accommodation cap for a night in Singapore?", ((*TRAVEL, "6.2"),)),
    Question(5, "How often do we refresh KYC for a high-risk client?", ((*KYC, "6.1"),)),
    Question(6, "What happens if a KYC refresh is more than 90 days overdue?", ((*KYC, "6.4"),)),
    Question(7, "At what ownership percentage do we identify beneficial owners under enhanced "
                "due diligence?", ((*KYC, "4.2"),)),
    Question(8, "How long do we keep client correspondence?",
             ((*RETENTION, "4.1"), (*RETENTION, "4.2"))),
    Question(9, "Who can approve a critical outsourcing arrangement?", ((*OUTSOURCING, "4.1"),)),
    Question(10, "A provider holds our client correspondence. How long can they keep it after "
                 "we terminate?", ((*OUTSOURCING, "6.4"), (*RETENTION, "4.1")), needs_all=True),
    Question(11, "Can I expense my partner's flight if they travel with me?"),
    Question(12, "What is our policy on cryptocurrency held by clients?"),
    Question(13, "How many days of paid parental leave am I entitled to?"),
]


def _matches(hit: Hit, expected: tuple[str, str, str]) -> bool:
    document_id, version, number = expected
    return (
        hit.document_id == document_id
        and hit.metadata.get("version") == version
        and hit.section.split(" ", 1)[0].rstrip(".") == number
    )


def ranks(question: Question, hits: list[Hit]) -> list[int | None]:
    """1-based rank of each expected section in the hits, or None if absent."""
    return [
        next((i + 1 for i, hit in enumerate(hits) if _matches(hit, expected)), None)
        for expected in question.expected
    ]


def in_top_three(question: Question, hits: list[Hit]) -> bool:
    found = [rank is not None and rank <= 3 for rank in ranks(question, hits)]
    return all(found) if question.needs_all else any(found)


def live_search(question: Question) -> list[Hit]:
    return search(question.text, store=get_vector_store(), embed=embed,
                  top_k=settings.retrieve_top_k)


def main() -> None:
    print(f"top_k={settings.retrieve_top_k}\n")
    print("| Q | top score | expected rank(s) | in top 3 | top hit |")
    print("|---|---|---|---|---|")
    for question in QUESTIONS:
        hits = live_search(question)
        top = hits[0]
        found = ", ".join(str(r) for r in ranks(question, hits)) if question.answerable else "—"
        ok = ("yes" if in_top_three(question, hits) else "NO") if question.answerable else "—"
        print(f"| {question.number} | {top.score:.3f} | {found} | {ok} | "
              f"{top.document_id} v{top.metadata.get('version')} {top.section} |")


if __name__ == "__main__":
    main()
