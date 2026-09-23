"""Retrieval over the indexed policy corpus.

Callers use get_vector_store(); they do not construct a client themselves.
"""

from __future__ import annotations

from functools import lru_cache

from app.retrieve.store import Hit, Passage, VectorStore

__all__ = ["Hit", "Passage", "VectorStore", "get_vector_store"]


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStore:
    """The application's vector store. One client, reused."""
    from app.retrieve.qdrant_store import QdrantVectorStore

    return QdrantVectorStore()
