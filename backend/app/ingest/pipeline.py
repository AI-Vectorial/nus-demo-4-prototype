"""Corpus to vector store: load, split, embed in batches, upsert.

Idempotent (REQ-I4): a passage's id is derived from its document, version,
section and text, so re-running upserts the same points onto themselves.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from pathlib import Path

from app.core.config import settings
from app.ingest.chunker import split
from app.ingest.loader import Document, Section, load_corpus
from app.retrieve.store import Passage, VectorStore

log = logging.getLogger(__name__)

CORPUS_DIR = Path(__file__).resolve().parents[2] / "corpus"

# Fixed, so ids are stable across machines and runs. Qdrant requires a UUID or
# an integer; uuid5 gives a UUID that is a hash of its input.
_ID_NAMESPACE = uuid.UUID("5b0c6f1e-6d0b-4c2e-9d57-a1d3e0c4f7b2")

Embed = Callable[[list[str]], list[list[float]]]


def _passage_id(doc: Document, section: Section, text: str) -> str:
    key = "\x1f".join([doc.id, doc.version, section.heading, text])
    return str(uuid.uuid5(_ID_NAMESPACE, key))


def _embedded_text(doc: Document, section: Section, text: str) -> str:
    """What gets embedded: the passage, prefixed with where it sits (D1).

    A thirty-word section on its own often lacks the words that say what it is
    about; its title and parent heading supply them.
    """
    path = " › ".join(p for p in (doc.title, section.parent, section.heading) if p)
    return f"{path}\n\n{text}"


def _pieces(documents: list[Document], max_tokens: int, overlap_tokens: int):
    for doc in documents:
        for section in doc.sections:
            for text in split(section.text, max_tokens, overlap_tokens):
                yield doc, section, text


def ingest(
    store: VectorStore,
    embed: Embed,
    *,
    corpus_dir: Path = CORPUS_DIR,
    force: bool = False,
    batch_size: int | None = None,
) -> int:
    """Index the corpus. Returns how many passages the store holds afterwards."""
    batch_size = batch_size or settings.embedding_batch_size
    documents = load_corpus(corpus_dir)
    pieces = list(_pieces(documents, settings.chunk_max_tokens, settings.chunk_overlap_tokens))

    if force:
        store.recreate()
    else:
        store.ensure_ready()

    for start in range(0, len(pieces), batch_size):
        batch = pieces[start : start + batch_size]
        vectors = embed([_embedded_text(doc, section, text) for doc, section, text in batch])
        store.upsert([
            Passage(
                id=_passage_id(doc, section, text),
                text=text,
                document_id=doc.id,
                document_title=doc.title,
                section=section.heading,
                embedding=vector,
                metadata={
                    "version": doc.version,
                    "status": doc.status,
                    "effective": doc.effective,
                    "owner": doc.owner,
                },
            )
            for (doc, section, text), vector in zip(batch, vectors, strict=True)
        ])
        log.info("embedded %d of %d passages", start + len(batch), len(pieces))

    return store.count()
