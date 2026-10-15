"""Run the evaluation set against the LIVE index. Needs Qdrant and the embedding model.

    cd backend && python -m tests.eval.run

Prints, for each question, the top three results and the best raw score, then
the two checks that matter:
  - F2 / REQ-R5: every answerable question has its expected section in the top three
  - F3 / D2:     the score gap between the weakest answerable question and the
                 strongest unanswerable one

This is a manual check, not a CI test: it calls the embedding provider.
"""

from __future__ import annotations

import sys

from app.generate import embed
from app.retrieve import get_vector_store
from app.retrieve.search import search
from tests.eval.questions import QUESTIONS, Question


def _section_number(heading: str) -> str:
    return heading.split(" ", 1)[0]


def _found(hits, document_id: str, number: str) -> bool:
    return any(h.document_id == document_id and _section_number(h.section) == number
               for h in hits)


def _passes_top_three(question: Question, hits) -> bool:
    if question.any_of:
        return any(_found(hits, d, n) for d, n in question.any_of)
    return all(_found(hits, d, n) for d, n in question.expected)


def main() -> int:
    store = get_vector_store()
    store.ensure_ready()

    answerable_best: list[tuple[str, float]] = []
    unanswerable_best: list[tuple[str, float]] = []
    failures: list[str] = []

    for question in QUESTIONS:
        [vector] = embed([question.text])
        raw = store.search(vector, limit=5)
        best = raw[0].score if raw else 0.0
        top3 = search(store, embed, question.text, top_k=3)

        print(f"\n{question.id}  {question.text}")
        print(f"    best raw score: {best:.4f}")
        for hit in top3:
            print(f"    {hit.score:.4f}  {hit.document_id} | {hit.section} | "
                  f"{hit.metadata.get('status')} {hit.metadata.get('version')}")

        if question.answerable:
            answerable_best.append((question.id, best))
            if not _passes_top_three(question, top3):
                failures.append(question.id)
                print("    FAIL: expected section not in top three")
            else:
                print("    pass")
        else:
            unanswerable_best.append((question.id, best))

    print("\n--- REQ-R5 (top three)")
    if failures:
        print(f"FAILED: {', '.join(failures)}")
    else:
        print("PASS: all answerable questions have the expected section in the top three")

    print("\n--- D2 separation")
    weakest = min(answerable_best, key=lambda pair: pair[1])
    strongest_no = max(unanswerable_best, key=lambda pair: pair[1])
    print(f"weakest answerable:    {weakest[0]} {weakest[1]:.4f}")
    print(f"strongest unanswerable: {strongest_no[0]} {strongest_no[1]:.4f}")
    print(f"margin (weakest yes - strongest no): {weakest[1] - strongest_no[1]:+.4f}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
