"""Ingestion: the policy corpus into the vector store.

    python -m app.ingest            index the corpus; re-running changes nothing
    python -m app.ingest --force    recreate the collection, re-embed everything
"""

from __future__ import annotations

from app.ingest.pipeline import CORPUS_DIR, ingest

__all__ = ["CORPUS_DIR", "ingest"]
