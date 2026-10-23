"""Ingestion: corpus -> sections -> embeddings -> the vector store.

Run it with `python -m app.ingest`. Re-running changes nothing (REQ-I4).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from app.core.config import settings
from app.ingest.loader import CORPUS_DIR, load_corpus
from app.retrieve.store import Passage, VectorStore

__all__ = ["CORPUS_DIR", "index_corpus", "load_corpus"]


def index_corpus(
    store: VectorStore,
    embed: Callable[[list[str]], list[list[float]]],
    corpus_dir: Path = CORPUS_DIR,
    batch_size: int | None = None,
) -> int:
    """Embed every section in batches and upsert it. Returns the passage count."""
    store.ensure_ready()
    size = batch_size or settings.embedding_batch_size
    passages = load_corpus(corpus_dir)

    embedded: list[Passage] = []
    for start in range(0, len(passages), size):
        batch = passages[start : start + size]
        vectors = embed([p.text for p in batch])
        embedded.extend(replace(p, embedding=v) for p, v in zip(batch, vectors, strict=True))

    return store.upsert(embedded)
