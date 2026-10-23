from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path
from uuid import UUID

from app.generate import embed
from app.ingest.chunker import chunk_section
from app.ingest.parser import parse_document
from app.retrieve import get_vector_store
from app.retrieve.store import Passage, VectorStore


def _passage_id(document_id: str, section: str, text: str) -> str:
    digest = hashlib.sha256(f"{document_id}\0{section}\0{text}".encode()).digest()
    return str(UUID(bytes=digest[:16]))


def ingest_corpus(
    corpus_dir: Path,
    store: VectorStore,
    *,
    max_tokens: int,
    overlap_tokens: int,
    embedding_model: str,
    force: bool = False,
    embed_texts: Callable[[list[str]], list[list[float]]] = embed,
) -> int:
    if force:
        store.recreate()
    store.ensure_ready()

    documents = [
        path for path in sorted(corpus_dir.glob("*.md"))
        if path.stem not in {"EVALUATION", "FICTION-AUDIT"}
    ]
    pending: list[tuple[str, str, str, dict[str, str]]] = []
    for path in documents:
        document = parse_document(path.read_text(encoding="utf-8"))
        for section in document.sections:
            for text in chunk_section(
                section.text,
                max_tokens,
                overlap_tokens,
                model=embedding_model,
            ):
                pending.append((document.metadata["id"], document.metadata["title"],
                                section.heading, {**document.metadata, "text": text}))

    vectors = embed_texts([entry[3]["text"] for entry in pending])
    if len(vectors) != len(pending):
        raise RuntimeError(
            "Embedding provider returned a different number of vectors than passages"
        )

    passages = [
        Passage(
            id=_passage_id(document_id, section, metadata["text"]),
            text=metadata["text"],
            document_id=document_id,
            document_title=title,
            section=section,
            embedding=vector,
            metadata={
                key: metadata[key]
                for key in ("version", "status", "effective", "owner")
            },
        )
        for (document_id, title, section, metadata), vector in zip(pending, vectors, strict=True)
    ]
    store.upsert(passages)
    return len(passages)


def ingest_default_corpus(*, force: bool = False) -> int:
    from app.core.config import settings

    if settings.chunk_max_tokens is None or settings.chunk_overlap_tokens is None:
        raise RuntimeError("CHUNK_MAX_TOKENS and CHUNK_OVERLAP_TOKENS must be configured")

    corpus_dir = Path(__file__).resolve().parents[2] / "corpus"
    return ingest_corpus(
        corpus_dir,
        get_vector_store(),
        max_tokens=settings.chunk_max_tokens,
        overlap_tokens=settings.chunk_overlap_tokens,
        embedding_model=settings.embedding_model_slug,
        force=force,
    )
