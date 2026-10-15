"""An in-memory vector store, for tests that must not need a running Qdrant.

Implements the same VectorStore interface the application uses, so a test
exercises your real retrieval code rather than a parallel implementation of it.

Similarity is cosine over the embeddings you put in, so scores behave the way
Qdrant's do and a threshold tuned here means something.
"""

from __future__ import annotations

import math

from app.retrieve.store import Hit, Passage


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return 0.0 if na == 0 or nb == 0 else dot / (na * nb)


class FakeVectorStore:
    """Everything the application asks of a vector store, in a dictionary."""

    def __init__(self) -> None:
        self._passages: dict[str, Passage] = {}
        self.ready = False

    def ensure_ready(self) -> None:
        self.ready = True

    def reset(self) -> None:
        self._passages.clear()
        self.ready = True

    def upsert(self, passages: list[Passage]) -> int:
        for passage in passages:
            self._passages[passage.id] = passage
        return len(passages)

    def search(
        self, embedding: list[float], limit: int = 5, min_score: float = 0.0
    ) -> list[Hit]:
        scored = [
            (_cosine(embedding, p.embedding), p)
            for p in self._passages.values()
        ]
        scored = [(s, p) for s, p in scored if s >= min_score]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [
            Hit(
                passage_id=p.id,
                text=p.text,
                document_id=p.document_id,
                document_title=p.document_title,
                section=p.section,
                score=score,
                metadata=dict(p.metadata),
            )
            for score, p in scored[:limit]
        ]

    def count(self) -> int:
        return len(self._passages)

    def health(self) -> tuple[bool, str]:
        return True, f"{self.count()} passages indexed (fake)"
