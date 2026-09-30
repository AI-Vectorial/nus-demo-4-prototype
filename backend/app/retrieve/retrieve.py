"""Retrieval, and the refusal rule.

retrieve() returns Grounded or Insufficient -- never a bare list. REQ-R3: a
refusal is a type, so nothing downstream can call the model on nothing by
accident. The threshold is MIN_SCORE (REQ-R4); passages below it are
discarded (REQ-R2), and if none survive the answer is Insufficient.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.core.config import settings
from app.retrieve.store import Hit, VectorStore

Embed = Callable[[list[str]], list[list[float]]]


@dataclass(frozen=True)
class Grounded:
    """Passages that scored at or above the threshold, best first. Never empty."""

    hits: list[Hit]

    def __post_init__(self) -> None:
        if not self.hits:
            raise ValueError("Grounded needs at least one passage; use Insufficient")


@dataclass(frozen=True)
class Insufficient:
    """Nothing scored at or above the threshold. The assistant refuses."""

    min_score: float


Retrieval = Grounded | Insufficient


def retrieve(
    question: str,
    store: VectorStore,
    embed: Embed,
    *,
    top_k: int | None = None,
    min_score: float | None = None,
) -> Retrieval:
    threshold = settings.min_score if min_score is None else min_score
    [vector] = embed([question])
    hits = store.search(vector, limit=top_k or settings.retrieve_top_k, min_score=threshold)
    # The store is asked to filter; this makes the rule hold whatever the store does.
    hits = [h for h in hits if h.score >= threshold]
    return Grounded(hits) if hits else Insufficient(min_score=threshold)
