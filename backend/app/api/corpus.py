"""GET /corpus and GET /corpus/{id} -- REQ-A4, REQ-B1, REQ-B3."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.schemas import DocumentSummary
from app.features import corpus

router = APIRouter()


@router.get("/corpus", response_model=list[DocumentSummary])
def list_corpus() -> list[dict]:
    return corpus.list_documents()


@router.get("/corpus/{document_key}", response_model=DocumentSummary)
def get_corpus_document(document_key: str) -> dict:
    found = corpus.get_document(document_key)
    if found is None:
        raise HTTPException(status_code=404, detail="document not found")
    return found
