"""F3 -- refuse. REQ-R2, REQ-R3, REQ-R4, REQ-R6. Decisions D2 and D5.

Retrieval returns one of two types, never an empty list:

    Grounded      passages above MIN_SCORE: the answer may be composed from these
    Insufficient  nothing above MIN_SCORE: the product refuses, and makes no model call

Generation takes a Grounded. It cannot be handed an Insufficient, so a refusal
cannot reach the model by accident (REQ-R3).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.core.config import settings
from app.retrieve.search import search
from app.retrieve.store import Hit, VectorStore

Embedder = Callable[[list[str]], list[list[float]]]

# D5: state the gap, and say where to go next. Same wording for every refusal.
REFUSAL_REASON = (
    "The policy documents do not cover this question, so I cannot give you an "
    "answer. For a decision on it, contact Group Finance."
)


@dataclass(frozen=True)
class Grounded:
    passages: list[Hit]


@dataclass(frozen=True)
class Insufficient:
    reason: str


Retrieval = Grounded | Insufficient


def ground(
    store: VectorStore,
    embed: Embedder,
    query: str,
    *,
    min_score: float | None = None,
) -> Retrieval:
    """Decide whether the corpus can support an answer to query."""
    threshold = settings.min_score if min_score is None else min_score
    hits = search(store, embed, query, min_score=threshold)
    if not hits:
        return Insufficient(REFUSAL_REASON)
    return Grounded(hits)
