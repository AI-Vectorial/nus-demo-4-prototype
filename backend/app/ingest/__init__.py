"""F1 -- ingest the policy corpus into the vector store.

Run it from the backend directory:

    python -m app.ingest           index the corpus; a second run changes nothing
    python -m app.ingest --force   recreate the collection and re-embed everything
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.ingest.chunk import CHARS_PER_TOKEN, split_sections, split_text
from app.ingest.corpus import Document, read_documents
from app.retrieve.store import Passage, VectorStore

__all__ = [
    "IngestResult",
    "build_passages",
    "embedding_text",
    "index_if_empty",
    "ingest",
    "read_documents",
    "split_sections",
    "split_text",
]

# Passage ids are derived from content, so a re-run produces the same ids and
# the upsert replaces rather than duplicates (REQ-I4).
_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "policy-assistant/passage")

Embedder = Callable[[list[str]], list[list[float]]]


@dataclass(frozen=True)
class IngestResult:
    documents: int
    passages: int
    indexed: int


def embedding_text(doc: Document, section: str, text: str) -> str:
    """What gets embedded: the document title and section, then the passage."""
    return f"{doc.title} — {section}\n\n{text}"


def build_passages(
    documents: list[Document], embed: Embedder, max_tokens: int | None = None
) -> list[Passage]:
    """Split, embed and label every passage. Nothing is written to the store."""
    tokens = settings.chunk_max_tokens if max_tokens is None else max_tokens
    limit_chars = tokens * CHARS_PER_TOKEN

    records: list[tuple[Document, str, str]] = []
    for document in documents:
        for section, body in split_sections(document.body):
            for text in split_text(body, limit_chars):
                records.append((document, section, text))

    if not records:
        return []

    # Amendment 2: the vector is built from the title and section heading as
    # well as the text, so a question about "refresh" can reach "Refresh
    # cycles". The stored text and citation fields are unchanged.
    vectors = embed([embedding_text(doc, section, text) for doc, section, text in records])
    return [
        Passage(
            id=str(uuid.uuid5(_NAMESPACE, f"{doc.id}|{doc.version}|{section}|{text}")),
            text=text,
            document_id=doc.id,
            document_title=doc.title,
            section=section,
            embedding=vector,
            metadata={"version": doc.version, "status": doc.status, "effective": doc.effective},
        )
        for (doc, section, text), vector in zip(records, vectors, strict=True)
    ]


def ingest(
    store: VectorStore,
    embed: Embedder,
    directory: Path | str | None = None,
    *,
    force: bool = False,
) -> IngestResult:
    if settings.chunk_overlap_tokens:
        # D1 is zero overlap. Refuse rather than silently ignore the setting.
        raise ValueError("CHUNK_OVERLAP_TOKENS is not supported: decision D1 is zero overlap")

    if force:
        store.reset()
    else:
        store.ensure_ready()

    documents = read_documents(Path(directory or settings.corpus_dir))
    passages = build_passages(documents, embed)
    indexed = store.upsert(passages)
    return IngestResult(documents=len(documents), passages=len(passages), indexed=indexed)


def index_if_empty(
    store: VectorStore,
    embed: Embedder,
    directory: Path | str | None = None,
) -> IngestResult | None:
    """Build the index only when the store holds nothing (F13).

    Used at startup, so a fresh deployment is never left with an empty index.
    Refreshing an existing index stays an explicit `python -m app.ingest`.
    Returns None when the store already had passages.
    """
    if store.count() > 0:
        return None
    return ingest(store, embed, directory)
