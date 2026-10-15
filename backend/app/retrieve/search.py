"""F2 -- find the passages nearest a question. REQ-R1, REQ-R5.

Decisions applied here:
- D3: RETRIEVE_TOP_K passages per question.
- D4: superseded passages are kept, but a current passage ranks ahead of any
  superseded one in the same result set.

Refusal is not decided here. That is F3, in app.retrieve.ground.
"""

from __future__ import annotations

from collections.abc import Callable

from app.core.config import settings
from app.retrieve.store import Hit, VectorStore

Embedder = Callable[[list[str]], list[list[float]]]

CURRENT = "current"


def prefer_current(hits: list[Hit]) -> list[Hit]:
    """Stable partition: current passages first, each group still best-first."""
    current = [h for h in hits if h.metadata.get("status") == CURRENT]
    superseded = [h for h in hits if h.metadata.get("status") != CURRENT]
    return current + superseded


def search(
    store: VectorStore,
    embed: Embedder,
    question: str,
    *,
    top_k: int | None = None,
    min_score: float = 0.0,
) -> list[Hit]:
    """Return up to top_k passages for the question, best first, with D4 applied.

    min_score is passed to the store, which drops weaker matches. Refusal on
    what remains is decided in app.retrieve.ground, not here.
    """
    limit = settings.retrieve_top_k if top_k is None else top_k
    [vector] = embed([question])
    return prefer_current(store.search(vector, limit=limit, min_score=min_score))[:limit]
