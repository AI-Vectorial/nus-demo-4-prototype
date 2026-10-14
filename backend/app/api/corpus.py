"""GET /corpus and GET /corpus/{id} -- the corpus browser's API (F7).

Read from backend/corpus/ on every start, never duplicated into the database
(REQ-B5). Both versions of the travel policy share an id, so a version can be
asked for; without one, the current version is served.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.ingest.corpus import documents

router = APIRouter(tags=["corpus"])


class SectionOut(BaseModel):
    heading: str
    text: str


class DocumentSummary(BaseModel):
    id: str
    title: str
    owner: str
    version: str
    effective: str
    status: str
    sections: list[str]


class DocumentOut(BaseModel):
    id: str
    title: str
    owner: str
    version: str
    effective: str
    status: str
    sections: list[SectionOut]


@router.get("/corpus", response_model=list[DocumentSummary])
def list_documents() -> list[DocumentSummary]:
    return [
        DocumentSummary(id=d.id, title=d.title, owner=d.owner, version=d.version,
                        effective=d.effective, status=d.status,
                        sections=[s.heading for s in d.sections])
        for d in sorted(documents(), key=lambda d: (d.title, d.status != "current"))
    ]


@router.get("/corpus/{document_id}", response_model=DocumentOut)
def get_document(document_id: str, version: str | None = None) -> DocumentOut:
    candidates = [d for d in documents() if d.id == document_id
                  and (d.version == version if version else d.status == "current")]
    if not candidates:
        raise HTTPException(status_code=404, detail="document not found")
    d = candidates[0]
    return DocumentOut(id=d.id, title=d.title, owner=d.owner, version=d.version,
                       effective=d.effective, status=d.status,
                       sections=[SectionOut(heading=s.heading, text=s.text) for s in d.sections])
