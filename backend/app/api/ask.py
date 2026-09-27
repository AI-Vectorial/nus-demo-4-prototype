"""POST /ask -- PRD section 5, exactly.

The route is thin: it validates the request, hands the question to
app.features.ask, and shapes the outcome. Its collaborators are FastAPI
dependencies so tests can substitute the fake store, model and database.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterator
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core import database
from app.core.config import settings
from app.features.ask import ConversationNotFound, ask
from app.generate import ProviderError, embed, generate
from app.ingest.__main__ import CORPUS_DIR
from app.retrieve import get_vector_store
from app.retrieve.store import VectorStore

router = APIRouter(tags=["ask"])


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    conversation_id: uuid.UUID | None = None

    @field_validator("question")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be blank")
        return value.strip()


class CitationOut(BaseModel):
    document_id: str
    document_title: str
    section: str
    version: str
    status: Literal["current", "superseded"]
    score: float


class AskResponse(BaseModel):
    outcome: Literal["answered", "refused", "degraded"]
    answer: str | None
    citations: list[CitationOut]
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    latency_ms: int


def get_db() -> Iterator[Session]:
    yield from database.get_session()


def get_store() -> VectorStore:
    return get_vector_store()


def get_embed() -> Callable[[list[str]], list[list[float]]]:
    return embed


def get_generate() -> Callable[..., str]:
    return generate


@router.post("/ask", response_model=AskResponse)
def post_ask(
    request: AskRequest,
    db: Annotated[Session, Depends(get_db)],
    store: Annotated[VectorStore, Depends(get_store)],
    embed_fn: Annotated[Callable, Depends(get_embed)],
    generate_fn: Annotated[Callable, Depends(get_generate)],
) -> AskResponse:
    try:
        result = ask(
            request.question,
            request.conversation_id,
            db=db,
            store=store,
            embed=embed_fn,
            generate=generate_fn,
            top_k=settings.retrieve_top_k,
            min_score=settings.min_score,
            model_name=settings.llm_model,
            generation_enabled=settings.generation_enabled,
            corpus_dir=CORPUS_DIR,
        )
    except ConversationNotFound as error:
        raise HTTPException(status_code=404, detail="conversation not found") from error
    except ProviderError as error:
        # Retrieval could not embed the question, so there is nothing to show --
        # not even degraded passages. An error, never dressed up as a refusal.
        raise HTTPException(status_code=503, detail="policy search is unavailable") from error

    return AskResponse(
        outcome=result.outcome,
        answer=result.answer,
        citations=[CitationOut(**vars(c)) for c in result.citations],
        conversation_id=result.conversation_id,
        message_id=result.message_id,
        latency_ms=result.latency_ms,
    )
