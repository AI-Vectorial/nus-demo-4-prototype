"""python -m app.retrieve.evaluate -- the score distribution D2 is chosen from.

Runs the thirteen questions in corpus/EVALUATION.md against the live index with
no threshold, plus the two follow-ups the team made criteria of (C14, C31), and
prints what each scored. It does not choose MIN_SCORE: the team does, from this
output, by the method recorded in docs/design/D2-refusal-threshold.md.

Two numbers matter per question, because the threshold is applied per passage:

  answerable  the score of the EXPECTED section -- it must survive the threshold
              and sit in the top three (C4)
  refusable   the top score of ANY passage -- it must fall below the threshold (C5)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.config import require, settings
from app.generate import embed
from app.retrieve import get_vector_store
from app.retrieve.retrieve import query_text

# Where corpus/EVALUATION.md says each answer lives: (document id, version,
# section number). Q8 accepts either section; Q10 needs both.
EXPECTED: dict[str, tuple[str, list[tuple[str, str, str]]]] = {
    "Q1": ("any", [("travel-expense-policy", "3.1", "4.2")]),
    "Q2": ("any", [("travel-expense-policy", "3.1", "4.2")]),
    "Q3": ("any", [("travel-expense-policy", "3.1", "5.2")]),
    "Q4": ("any", [("travel-expense-policy", "3.1", "6.2")]),
    "Q5": ("any", [("client-onboarding-kyc", "2.4", "6.1")]),
    "Q6": ("any", [("client-onboarding-kyc", "2.4", "6.4")]),
    "Q7": ("any", [("client-onboarding-kyc", "2.4", "4.2")]),
    "Q8": ("any", [("records-retention", "4.0", "4.1"), ("records-retention", "4.0", "4.2")]),
    "Q9": ("any", [("outsourcing-third-party", "1.8", "4.1")]),
    "Q10": ("all", [("outsourcing-third-party", "1.8", "6.4"),
                    ("records-retention", "4.0", "4.1")]),
}
REFUSE = ["Q11", "Q12", "Q13"]

# The follow-ups in tickets/T1.md, searched as D9 searches them.
C14 = ["What is the approval limit for travel expenses?", "What about expenses above that limit?"]


@dataclass
class Row:
    label: str
    kind: str  # answerable | refusable
    score: float  # expected-section score, or top score
    rank: int | None
    top3: list[str]


def questions() -> dict[str, str]:
    text = (settings.corpus_dir / "EVALUATION.md").read_text(encoding="utf-8")
    return dict(re.findall(r"^### (Q\d+) — (?:⭐ )?(.+?)\s*$", text, re.MULTILINE))


def _key(hit) -> tuple[str, str, str]:
    return (hit.document_id, hit.metadata.get("version", ""), hit.section.split(" ")[0])


def _label(hit) -> str:
    return f"{hit.document_id} v{hit.metadata.get('version')} {hit.section} ({hit.score:.3f})"


def measure(label: str, asked: list[str], kind: str) -> Row:
    vector = embed([query_text(asked)])[0]
    hits = get_vector_store().search(vector, limit=require(settings.retrieve_top_k,
                                                           "RETRIEVE_TOP_K"))
    top3 = [_label(h) for h in hits[:3]]
    if kind == "refusable":
        return Row(label, kind, hits[0].score if hits else 0.0, None, top3)

    mode, wanted = EXPECTED.get(label, EXPECTED["Q1"])
    found: dict[tuple[str, str, str], tuple[int, float]] = {}
    for i, h in enumerate(hits):
        if _key(h) in wanted:
            found.setdefault(_key(h), (i + 1, h.score))
    if not found or (mode == "all" and len(found) < len(wanted)):
        return Row(label, kind, 0.0, None, top3)
    # "any": the best-placed expected section. "all": the weakest of them,
    # since that is the one the threshold must still let through.
    rank, score = max(found.values()) if mode == "all" else min(found.values())
    return Row(label, kind, score, rank, top3)


def main() -> None:
    asked = questions()
    rows = [measure(q, [asked[q]], "answerable") for q in EXPECTED]
    rows.append(measure("C14 follow-up", C14, "answerable"))
    rows += [measure(q, [asked[q]], "refusable") for q in REFUSE]
    rows.append(measure("C31 Q1→Q11", [asked["Q1"], asked["Q11"]], "refusable"))

    print(f"{'':16} {'kind':10} {'score':>6} {'rank':>4}  top three")
    for r in rows:
        rank = "-" if r.rank is None else str(r.rank)
        print(f"{r.label:16} {r.kind:10} {r.score:6.3f} {rank:>4}  {r.top3[0] if r.top3 else ''}")
        for other in r.top3[1:]:
            print(f"{'':44}{other}")

    floor = min(r.score for r in rows if r.kind == "answerable")
    ceiling = max(r.score for r in rows if r.kind == "refusable")
    missed = [r.label for r in rows if r.kind == "answerable" and (r.rank is None or r.rank > 3)]
    print()
    print(f"lowest expected-section score (must pass)  {floor:.3f}")
    print(f"highest top score that must refuse         {ceiling:.3f}")
    print(f"gap                                        {floor - ceiling:+.3f}")
    print(f"expected section outside the top three     {missed or 'none'}")


if __name__ == "__main__":
    main()
