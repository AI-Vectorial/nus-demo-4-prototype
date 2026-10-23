"""Retrieval: embed a question, return the closest passages, best first.

No threshold here. Discarding weak matches and refusing is F3's job, so this
returns whatever the store finds in the top K.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.core.config import settings
from app.retrieve.store import Hit, VectorStore


@dataclass(frozen=True)
class Grounded:
    """Retrieval found at least one passage above the threshold. Never empty."""

    hits: list[Hit]


@dataclass(frozen=True)
class Insufficient:
    """Nothing cleared the threshold. Generation must not run on this."""

    reason: str


Retrieval = Grounded | Insufficient


def retrieve_grounded(
    question: str,
    store: VectorStore,
    embed: Callable[[list[str]], list[list[float]]],
    *,
    min_score: float | None = None,
    limit: int | None = None,
) -> Retrieval:
    """Passages above the threshold, or an explicit refusal. REQ-R2, R3, R4."""
    threshold = min_score if min_score is not None else settings.min_score
    if threshold is None:
        raise ValueError(
            "MIN_SCORE is not set. The refusal threshold is decision D2; set it in "
            "the environment after measuring corpus/EVALUATION.md."
        )
    vector = embed([question])[0]
    hits = store.search(
        vector,
        limit=limit if limit is not None else settings.retrieve_top_k,
        min_score=threshold,
    )
    if not hits:
        return Insufficient(
            reason="No passage in the policy set matches this question closely enough."
        )
    return Grounded(hits=hits)


def retrieve(
    question: str,
    store: VectorStore,
    embed: Callable[[list[str]], list[list[float]]],
    limit: int | None = None,
) -> list[Hit]:
    """The closest passages to the question. REQ-R1."""
    vector = embed([question])[0]
    return store.search(vector, limit=limit if limit is not None else settings.retrieve_top_k)
