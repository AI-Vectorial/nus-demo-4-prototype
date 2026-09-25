"""Indexing the policy corpus.

Run as a command -- `python -m app.ingest` -- or called as ingest(). Callers
need those two names and CorpusError; the loader and chunker are detail.
"""

from __future__ import annotations

from app.ingest.loader import CorpusError
from app.ingest.pipeline import ingest

__all__ = ["CorpusError", "ingest"]
