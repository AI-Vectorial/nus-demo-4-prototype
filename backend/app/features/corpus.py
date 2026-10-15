"""F7 -- corpus browser. REQ-B1 to REQ-B5, REQ-A4.

Documents are read from backend/corpus/ on each request (REQ-B5). Nothing is
copied into the database.

A corpus entry's id is "{document_id}-{version}". The two travel policy versions
share a document_id, so the version is needed to tell them apart. A citation
carries both, so it can be linked to its exact version (REQ-U15).
"""

from __future__ import annotations

from pathlib import Path

from app.core.config import settings
from app.ingest.chunk import split_sections
from app.ingest.corpus import Document, read_documents


def _key(document: Document) -> str:
    return f"{document.id}-{document.version}"


def _view(document: Document) -> dict:
    return {
        "id": _key(document),
        "title": document.title,
        "owner": document.owner,
        "version": document.version,
        "effective": document.effective,
        "status": document.status,
        "sections": [
            {"heading": heading, "text": text}
            for heading, text in split_sections(document.body)
        ],
    }


def list_documents(directory: Path | str | None = None) -> list[dict]:
    return [_view(d) for d in read_documents(Path(directory or settings.corpus_dir))]


def get_document(key: str, directory: Path | str | None = None) -> dict | None:
    for document in read_documents(Path(directory or settings.corpus_dir)):
        if _key(document) == key:
            return _view(document)
    return None
