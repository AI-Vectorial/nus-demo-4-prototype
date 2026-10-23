from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.features.ask import ask_policy

router = APIRouter(tags=["assistant"])


class AskRequest(BaseModel):
    question: str
    conversation_id: UUID | None = None

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be blank")
        return value.strip()


class CitationResponse(BaseModel):
    document_id: str
    document_title: str
    section: str
    version: str
    status: Literal["current", "superseded"]
    score: float


class AskResponse(BaseModel):
    outcome: Literal["answered", "refused", "degraded"]
    answer: str | None
    citations: list[CitationResponse]
    conversation_id: UUID
    message_id: UUID
    latency_ms: int


@router.post("/ask", response_model=AskResponse)
def ask(
    request: AskRequest,
    session: Annotated[Session, Depends(get_session)],
) -> AskResponse:
    return AskResponse(
        **ask_policy(session, request.question, request.conversation_id)
    )
