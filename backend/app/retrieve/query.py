from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.core.config import settings
from app.generate import embed
from app.retrieve import get_vector_store
from app.retrieve.store import Hit, VectorStore


@dataclass(frozen=True)
class Grounded:
    hits: list[Hit]


@dataclass(frozen=True)
class Insufficient:
    best_score: float | None


RetrievalResult = Grounded | Insufficient


def retrieve_candidates(
    query_text: str,
    *,
    store: VectorStore | None = None,
    embed_texts: Callable[[list[str]], list[list[float]]] = embed,
    limit: int | None = None,
) -> list[Hit]:
    if not query_text.strip():
        raise ValueError("query_text must not be empty")
    result_limit = limit if limit is not None else settings.retrieve_top_k
    if result_limit is None or result_limit <= 0:
        raise RuntimeError("RETRIEVE_TOP_K must be configured as a positive integer")
    vectors = embed_texts([query_text])
    if len(vectors) != 1:
        raise RuntimeError("Embedding provider must return exactly one query vector")
    vector_store = store or get_vector_store()
    return vector_store.search(vectors[0], limit=result_limit)


def retrieve(
    query_text: str,
    *,
    store: VectorStore | None = None,
    embed_texts: Callable[[list[str]], list[list[float]]] = embed,
    min_score: float | None = None,
    limit: int | None = None,
) -> RetrievalResult:
    threshold = min_score if min_score is not None else settings.min_score
    if threshold is None:
        raise RuntimeError("MIN_SCORE must be calibrated and configured before retrieval")
    candidates = retrieve_candidates(
        query_text,
        store=store,
        embed_texts=embed_texts,
        limit=limit,
    )
    grounded = [hit for hit in candidates if hit.score >= threshold]
    if not grounded:
        return Insufficient(best_score=candidates[0].score if candidates else None)
    return Grounded(hits=grounded)
