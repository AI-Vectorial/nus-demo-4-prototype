"""Corpus to indexed passages, in one call.

Load, validate, chunk, embed, upsert. The order matters: validation happens
before anything is embedded, so a corpus that has drifted from its manifest
costs nothing and fails immediately rather than half-writing a collection.
"""

from __future__ import annotations

import logging

from app.generate import embed
from app.ingest.chunker import Chunk, chunk_corpus
from app.ingest.loader import load_corpus
from app.retrieve import get_vector_store
from app.retrieve.store import Passage

log = logging.getLogger(__name__)


def ingest(force: bool = False) -> dict[str, int]:
    """Index the whole corpus. Returns documents, passages and skipped counts.

    `skipped` is how many passages were already indexed under the same id --
    the evidence for REQ-I4. A second run with an unchanged corpus reports
    every passage skipped and leaves the count where it was.
    """
    documents = load_corpus()
    chunks = chunk_corpus(documents)
    log.info("loaded %d documents, %d passages", len(documents), len(chunks))

    store = get_vector_store()
    if force:
        store.recreate()
    store.ensure_ready()

    before = store.count()
    passages = _embedded(chunks)
    store.upsert(passages)
    after = store.count()

    # Anything that did not grow the collection replaced a point already
    # holding the same id, and therefore the same text.
    skipped = len(passages) - (after - before)

    return {
        "documents": len(documents),
        "passages": len(passages),
        "skipped": skipped,
    }


def _embedded(chunks: list[Chunk]) -> list[Passage]:
    """Chunks with their vectors. embed() batches, so this is one pass (REQ-I6)."""
    vectors = embed([chunk.text for chunk in chunks])
    return [
        Passage(
            id=chunk.id,
            text=chunk.text,
            document_id=chunk.document_id,
            document_title=chunk.document_title,
            section=chunk.section,
            embedding=vector,
            # Flattened into the Qdrant payload alongside the fields above,
            # which together are the contract in PRD section 7.
            metadata={
                "version": chunk.version,
                "status": chunk.status,
                "effective": chunk.effective,
            },
        )
        for chunk, vector in zip(chunks, vectors, strict=True)
    ]
