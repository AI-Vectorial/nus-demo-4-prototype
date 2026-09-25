"""Choose MIN_SCORE against the evaluation set, and show the working.

PRD decision D2 asks how the refusal threshold was arrived at, and "it felt
right" is not an answer. This runs all thirteen questions in
corpus/EVALUATION.md against the real index, prints the score distribution,
and recommends the value that separates the ten answerable questions from the
three that must refuse.

A script rather than a test, deliberately: it needs a live Qdrant and a live
OpenRouter key, and a test suite that needs the network is a test suite that
gets skipped.

    cd backend
    .venv/Scripts/python.exe scripts/tune_threshold.py

Nothing here writes anything. The number it prints goes in MIN_SCORE, and the
table it prints goes in EVALUATION.md's results section by hand -- that file
is protected, and filling it in is the team's evidence, not the script's.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
EVALUATION = BACKEND / "corpus" / "EVALUATION.md"

# Q1-Q10 are answerable; Q11-Q13 must refuse. Fixed by the evaluation set.
LAST_ANSWERABLE = 10

QUESTION_HEADING = re.compile(r"^###\s+Q(\d+)\s+[-—]+\s*(.+?)\s*$")
EXPECTED_SECTION = re.compile(r"^\*\*Sections?:\*\*\s*(.+?)\s*$")


class Question:
    """One evaluation question and what the corpus says about it."""

    def __init__(self, number: int, text: str) -> None:
        self.number = number
        self.text = text.lstrip("⭐ ").strip()
        self.sections: list[str] = []

    @property
    def answerable(self) -> bool:
        return self.number <= LAST_ANSWERABLE

    def expects(self, section: str) -> bool:
        """Does a retrieved section match one this question should find?

        Loose on purpose: EVALUATION.md writes some expectations as
        "4.1 General table / 4.2 Client correspondence", and a heading may be
        chunked with a suffix. Leading number is what has to agree.
        """
        found = section.strip().lower()
        return any(
            found.startswith(expected.lower()) or expected.lower().startswith(found)
            for expected in self.sections
            if expected
        )


def parse_questions(path: Path) -> list[Question]:
    """Pull the thirteen questions out of the evaluation set."""
    questions: list[Question] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        heading = QUESTION_HEADING.match(line)
        if heading:
            questions.append(Question(int(heading.group(1)), heading.group(2)))
            continue
        expected = EXPECTED_SECTION.match(line)
        if expected and questions:
            questions[-1].sections = [
                part.strip() for part in expected.group(1).split("/") if part.strip()
            ]
    return questions


def recommend(answerable: list[float], refusable: list[float]) -> tuple[float, str]:
    """A threshold that separates the two groups, and why it is that one.

    The weakest question that must be answered sets the ceiling; the strongest
    question that must refuse sets the floor. If they cross there is no clean
    number, and the plan says which way to err: refusing slightly too often is
    recoverable, a confident invention is not.
    """
    ceiling = min(answerable) if answerable else 0.0
    floor = max(refusable) if refusable else 0.0

    if ceiling > floor:
        # Midpoint of the gap: the furthest from both kinds of mistake.
        value = round((ceiling + floor) / 2, 2)
        return value, (
            f"separates cleanly -- weakest answerable {ceiling:.3f}, "
            f"strongest refusable {floor:.3f}"
        )

    value = round(floor + 0.01, 2)
    return value, (
        f"NO clean separation -- weakest answerable {ceiling:.3f} is not above "
        f"strongest refusable {floor:.3f}. This value refuses everything below "
        "the strongest out-of-scope question, so it refuses too often rather "
        "than inventing. Say so when defending D2; do not hide it."
    )


def main() -> int:
    sys.path.insert(0, str(BACKEND))

    from app.core.config import settings
    from app.generate import embed
    from app.retrieve import get_vector_store

    questions = parse_questions(EVALUATION)
    if len(questions) != 13:
        print(f"expected 13 questions in {EVALUATION.name}, parsed {len(questions)}")
        return 1

    store = get_vector_store()
    indexed = store.count()
    if not indexed:
        print("the collection is empty -- run `python -m app.ingest` first")
        return 1

    print(f"{indexed} passages in {settings.qdrant_collection}")
    print(f"MIN_SCORE is currently {settings.min_score}, "
          f"RETRIEVE_TOP_K is {settings.retrieve_top_k}\n")

    header = f"{'Q':>3}  {'top':>6}  {'3rd':>6}  {'top 3?':>6}  question"
    print(header)
    print("-" * len(header))

    tops: dict[int, float] = {}
    misplaced: list[int] = []

    for question in questions:
        hits = get_vector_store().search(
            embed([question.text])[0],
            limit=max(settings.retrieve_top_k, 3),
            min_score=0.0,
        )
        scores = [hit.score for hit in hits]
        top = scores[0] if scores else 0.0
        third = scores[2] if len(scores) > 2 else 0.0
        tops[question.number] = top

        if question.answerable and question.sections:
            found = any(question.expects(hit.section) for hit in hits[:3])
            if not found:
                misplaced.append(question.number)
            mark = "yes" if found else "NO"
        else:
            mark = "refuse" if not question.answerable else "-"

        print(f"{question.number:>3}  {top:6.3f}  {third:6.3f}  {mark:>6}  "
              f"{question.text[:64]}")

    answerable = [tops[q.number] for q in questions if q.answerable]
    refusable = [tops[q.number] for q in questions if not q.answerable]

    print()
    print(f"answerable  (Q1-Q{LAST_ANSWERABLE}) : "
          f"min {min(answerable):.3f}  max {max(answerable):.3f}")
    print(f"must refuse (Q{LAST_ANSWERABLE + 1}-Q{len(questions)}): "
          f"min {min(refusable):.3f}  max {max(refusable):.3f}")

    value, why = recommend(answerable, refusable)
    print(f"\nrecommended MIN_SCORE={value}  ({why})")

    if misplaced:
        # REQ-R5 is a retrieval problem, not a threshold one -- and the corpus
        # is protected, so the fix is chunking or top-k, never the question.
        print(f"\nREQ-R5 not met for Q{', Q'.join(str(n) for n in misplaced)}: "
              "the expected section was not in the top three. That is chunking "
              "or RETRIEVE_TOP_K, not the threshold.")

    would_answer = [q for q in questions if tops[q.number] >= value]
    wrong = [
        q.number for q in would_answer if not q.answerable
    ] + [
        q.number for q in questions if q.answerable and tops[q.number] < value
    ]
    print(f"at {value}: {len(would_answer)} answered, "
          f"{len(questions) - len(would_answer)} refused, "
          f"{len(wrong)} wrong ({wrong or 'none'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
