"""Retrieval: grounded passages or an explicit insufficiency (F2).

Never an empty list (REQ-R3). Generation accepts only Grounded, so a refusal
cannot reach the model by accident -- the types will not line up.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.retrieve.store import Hit, VectorStore


@dataclass(frozen=True)
class Grounded:
    """At least one passage at or above MIN_SCORE, best first."""

    hits: tuple[Hit, ...]

    def __post_init__(self) -> None:
        if not self.hits:
            raise ValueError("Grounded needs at least one passage; use Insufficient")


@dataclass(frozen=True)
class Insufficient:
    """Nothing scored at or above MIN_SCORE. The assistant refuses."""


Retrieval = Grounded | Insufficient


def query_text(questions: list[str]) -> str:
    """The text a question is searched with: it and the questions before it
    in the window (REQ-C7, D9), oldest first."""
    return "\n".join(questions)


def retrieve(text: str, store: VectorStore, embed: Callable[[list[str]], list[list[float]]],
             *, top_k: int, min_score: float) -> Retrieval:
    """Search on every turn (REQ-C5). Each passage below min_score is dropped
    (REQ-R2, D2: per passage, not only the top score)."""
    vector = embed([text])[0]
    hits = store.search(vector, limit=top_k, min_score=min_score)
    return Grounded(tuple(hits)) if hits else Insufficient()
