"""POST /ask -- the endpoint that makes it a product (F5). PRD section 5, fixed.

Retrieval runs on every turn (REQ-C5), on the user questions in the D8/D9
window. What happens next is decided in code, never by the model:

  Insufficient          refused   -- the D5 text, and no model call (C7)
  Grounded + answer     answered  -- citations are every passage the model was given (D7)
  Grounded, no model    degraded  -- the passages, no answer (REQ-G6)

The question's text is stored, because history needs it, and never logged (NFR-6).
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import MissingSetting, require, settings
from app.core.database import get_session
from app.core.models import Conversation, Message, MessageCitation
from app.features.context import Turn, retrieval_questions, window
from app.features.refuse import REFUSAL_VERSION, refusal
from app.generate import ProviderError, embed, generate
from app.generate.answer import Answered, compose
from app.ingest import corpus
from app.retrieve import get_vector_store
from app.retrieve.retrieve import Insufficient, query_text, retrieve
from app.retrieve.store import Hit, VectorStore

log = logging.getLogger(__name__)
router = APIRouter(tags=["ask"])


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    conversation_id: uuid.UUID | None = None


class Citation(BaseModel):
    document_id: str
    document_title: str
    section: str
    version: str
    status: Literal["current", "superseded"]
    score: float
    # Added to the section 5 shape, which allows additions: in degraded mode the
    # passage text is all the user gets, so it travels with the citation.
    text: str | None = None


class AskResponse(BaseModel):
    outcome: Literal["answered", "refused", "degraded"]
    answer: str | None
    citations: list[Citation]
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    latency_ms: int


@dataclass(frozen=True)
class AskDeps:
    """Everything /ask reaches outside itself, so a test can supply fakes."""

    store: VectorStore
    embed: Callable[[list[str]], list[list[float]]]
    generate: Callable[..., str]
    documents: list[corpus.Document]
    top_k: int
    min_score: float
    context_messages: int
    generation_enabled: bool
    model_name: str


@lru_cache(maxsize=1)
def _documents() -> list[corpus.Document]:
    return corpus.load(settings.corpus_dir)


def get_deps() -> AskDeps:
    try:
        return AskDeps(
            store=get_vector_store(),
            embed=embed,
            generate=generate,
            documents=_documents(),
            top_k=require(settings.retrieve_top_k, "RETRIEVE_TOP_K"),
            min_score=require(settings.min_score, "MIN_SCORE"),
            context_messages=settings.context_messages,
            generation_enabled=settings.generation_enabled,
            model_name=settings.llm_model,
        )
    except MissingSetting as missing:
        # Unanswerable until the team sets it -- never a guessed default.
        raise HTTPException(status_code=503, detail=str(missing)) from missing


def _citation(hit: Hit, *, with_text: bool) -> Citation:
    return Citation(
        document_id=hit.document_id,
        document_title=hit.document_title,
        section=hit.section,
        version=str(hit.metadata.get("version", "")),
        status=hit.metadata.get("status", "current"),
        score=round(hit.score, 4),
        text=hit.text if with_text else None,
    )


def _conversation(db: Session, conversation_id: uuid.UUID | None) -> Conversation:
    if conversation_id is None:
        conversation = Conversation()
        db.add(conversation)
        return conversation
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="conversation not found")
    return conversation


def _history(db: Session, conversation: Conversation, limit: int) -> list[Turn]:
    rows = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    ).all()
    return [Turn(m.role, m.content or "") for m in reversed(rows)]


@router.post("/ask", response_model=AskResponse)
def ask(body: AskRequest, db: Annotated[Session, Depends(get_session)],
        deps: Annotated[AskDeps, Depends(get_deps)]) -> AskResponse:
    started = time.perf_counter()
    conversation = _conversation(db, body.conversation_id)
    history = _history(db, conversation, deps.context_messages) if body.conversation_id else []
    turns = window(history, body.question, size=deps.context_messages)

    try:
        found = retrieve(query_text(retrieval_questions(turns)), deps.store, deps.embed,
                         top_k=deps.top_k, min_score=deps.min_score)
    except ProviderError as error:
        # Without an embedding there is nothing to search, so nothing to show:
        # an error, distinct from a refusal and from degraded mode.
        log.warning("search unavailable: %s", type(error).__name__)
        raise HTTPException(status_code=503, detail="policy search is unavailable") from error

    assistant = Message(role="assistant")
    if isinstance(found, Insufficient):
        assistant.outcome, assistant.content = "refused", refusal(deps.documents)
        assistant.prompt_version = REFUSAL_VERSION
        citations: list[Citation] = []
    else:
        result = compose(body.question, turns[:-1], found, deps.generate,
                         enabled=deps.generation_enabled, model_name=deps.model_name)
        if isinstance(result, Answered):
            assistant.outcome, assistant.content = "answered", result.text
            assistant.model, assistant.prompt_version = result.model, result.prompt_version
        else:
            assistant.outcome = "degraded"
        citations = [_citation(h, with_text=assistant.outcome == "degraded") for h in found.hits]

    now = datetime.now(UTC)
    assistant.latency_ms = round((time.perf_counter() - started) * 1000)
    assistant.citations = [
        MessageCitation(**c.model_dump(exclude={"text"})) for c in citations
    ]
    question = Message(role="user", content=body.question, created_at=now)
    assistant.created_at = datetime.now(UTC)
    conversation.messages.extend([question, assistant])
    conversation.last_at = assistant.created_at
    db.flush()

    log.info("ask conversation=%s outcome=%s citations=%d latency_ms=%d",
             conversation.id, assistant.outcome, len(citations), assistant.latency_ms)
    return AskResponse(
        outcome=assistant.outcome,
        answer=assistant.content,
        citations=citations,
        conversation_id=conversation.id,
        message_id=assistant.id,
        latency_ms=assistant.latency_ms,
    )
