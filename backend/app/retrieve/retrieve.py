"""Question in, grounded passages or an explicit insufficiency out.

REQ-R3 makes refusal a type rather than an empty list. Generation accepts only
Grounded, so it cannot be handed a refusal by accident: an empty Grounded
cannot be constructed, and Insufficient has no passages to compose from.

The threshold (D2) is applied here, in code, and nowhere else. A model is never
asked whether it knows enough to answer -- brief section 9.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.retrieve.store import Hit, VectorStore

Embed = Callable[[list[str]], list[list[float]]]


@dataclass(frozen=True)
class Grounded:
    """At least one passage scored at or above the threshold. Best first."""

    hits: tuple[Hit, ...]

    def __post_init__(self) -> None:
        if not self.hits:
            raise ValueError("Grounded needs at least one passage; use Insufficient")


@dataclass(frozen=True)
class Insufficient:
    """Nothing scored at or above the threshold. The assistant must refuse."""

    best_score: float | None


Retrieval = Grounded | Insufficient


def search(question: str, *, store: VectorStore, embed: Embed, top_k: int) -> list[Hit]:
    """The closest passages with their scores, before any threshold. REQ-R1."""
    [vector] = embed([question])
    return store.search(vector, limit=top_k)


def retrieve(
    question: str, *, store: VectorStore, embed: Embed, top_k: int, min_score: float
) -> Retrieval:
    """Search, then discard everything below the threshold. REQ-R2."""
    hits = search(question, store=store, embed=embed, top_k=top_k)
    kept = tuple(hit for hit in hits if hit.score >= min_score)
    if kept:
        return Grounded(kept)
    return Insufficient(best_score=hits[0].score if hits else None)
