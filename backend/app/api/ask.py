"""POST /ask -- a question in, one of three outcomes out. PRD section 5.

The record is written once the outcome is known, in one transaction: the
question and its answer, refusal or degraded result together (plan P1). A
conversation never holds half a turn.
"""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy.orm import sessionmaker

from app import generate as model_client
from app.core import database
from app.core.config import settings
from app.core.models import Conversation, Message, MessageCitation
from app.features.ask import Answered, Degraded, Refused, answer_question
from app.generate import ProviderError
from app.retrieve import Hit, VectorStore, get_vector_store

router = APIRouter(tags=["ask"])


class AskRequest(BaseModel):
    question: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1,
                                               max_length=2000)]
    conversation_id: uuid.UUID | None = None


class Citation(BaseModel):
    document_id: str
    document_title: str
    section: str
    version: str
    status: Literal["current", "superseded"]
    score: float


class AskResponse(BaseModel):
    outcome: Literal["answered", "refused", "degraded"]
    answer: str | None
    citations: list[Citation] = Field(default_factory=list)
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    latency_ms: int


# Dependencies, so tests can substitute each one.

def get_sessions() -> sessionmaker:
    if database.SessionLocal is None:
        raise HTTPException(503, "The database is not configured.")
    return database.SessionLocal


def get_store() -> VectorStore:
    return get_vector_store()


def get_model() -> SimpleNamespace:
    return SimpleNamespace(embed=model_client.embed, generate=model_client.generate)


def get_min_score() -> float:
    return settings.min_score


def _citation(hit: Hit) -> Citation:
    return Citation(
        document_id=hit.document_id,
        document_title=hit.document_title,
        section=hit.section,
        version=str(hit.metadata.get("version", "")),
        status=hit.metadata.get("status", "current"),
        score=round(hit.score, 4),
    )


@router.post("/ask", response_model=AskResponse)
def ask(
    body: AskRequest,
    sessions: Annotated[sessionmaker, Depends(get_sessions)],
    store: Annotated[VectorStore, Depends(get_store)],
    model: Annotated[SimpleNamespace, Depends(get_model)],
    min_score: Annotated[float, Depends(get_min_score)],
) -> AskResponse:
    started = time.monotonic()
    asked_at = datetime.now(UTC)

    with sessions.begin() as db:
        if body.conversation_id is None:
            conversation = Conversation(started_at=asked_at)
            db.add(conversation)
        else:
            conversation = db.get(Conversation, body.conversation_id)
            if conversation is None:
                raise HTTPException(404, "No such conversation.")

        try:
            outcome = answer_question(body.question, store, model.embed, model.generate,
                                      min_score=min_score)
        except ProviderError as error:
            # The question could not even be embedded, so there is nothing
            # retrieved to degrade to. An error, not a refusal -- and nothing
            # is recorded, because nothing was answered.
            raise HTTPException(503, "Policy search is unavailable. Try again shortly.") \
                from error

        latency_ms = int((time.monotonic() - started) * 1000)
        citations = [] if isinstance(outcome, Refused) else [_citation(h)
                                                             for h in outcome.citations]
        answered = isinstance(outcome, Answered)
        reply = Message(
            role="assistant",
            outcome=("answered" if answered
                     else "degraded" if isinstance(outcome, Degraded) else "refused"),
            content=None if isinstance(outcome, Degraded) else outcome.text,
            model=outcome.model if answered else None,
            prompt_version=outcome.prompt_version if answered else None,
            latency_ms=latency_ms,
            citations=[MessageCitation(**c.model_dump()) for c in citations],
        )
        conversation.messages.extend([
            Message(role="user", content=body.question, created_at=asked_at),
            reply,
        ])
        conversation.last_at = datetime.now(UTC)
        db.flush()

        return AskResponse(
            outcome=reply.outcome,
            answer=reply.content,
            citations=citations,
            conversation_id=conversation.id,
            message_id=reply.id,
            latency_ms=latency_ms,
        )
