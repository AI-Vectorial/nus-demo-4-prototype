"""Retrieval: embed a question, return the closest passages, best first.

No threshold here. Discarding weak matches and refusing is F3's job, so this
returns whatever the store finds in the top K.
"""

from __future__ import annotations

from collections.abc import Callable

from app.core.config import settings
from app.retrieve.store import Hit, VectorStore


def retrieve(
    question: str,
    store: VectorStore,
    embed: Callable[[list[str]], list[list[float]]],
    limit: int | None = None,
) -> list[Hit]:
    """The closest passages to the question. REQ-R1."""
    vector = embed([question])[0]
    return store.search(vector, limit=limit if limit is not None else settings.retrieve_top_k)
