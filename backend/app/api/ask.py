"""POST /ask -- one question, one of three outcomes, every turn recorded.

Retrieval refuses or grounds. Grounded questions are composed, or degrade to the
passages when generation is off or the provider is down. The outcome is explicit
in the response; a client never infers it from a null answer (PRD §5).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterator
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import session_scope
from app.generate import embed as provider_embed
from app.generate import generate as provider_generate
from app.generate.client import ProviderError
from app.generate.compose import Answered, compose
from app.models.record import Conversation, Message, MessageCitation
from app.retrieve import get_vector_store
from app.retrieve.search import Grounded, retrieve_grounded
from app.retrieve.store import Hit, VectorStore

router = APIRouter(tags=["ask"])


class AskRequest(BaseModel):
    question: str
    conversation_id: str | None = None


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
    citations: list[Citation]
    conversation_id: str
    message_id: str
    latency_ms: int
    notice: str | None = None


# --- dependencies: each one is replaceable in tests -------------------------

def get_db() -> Iterator[Session]:
    with session_scope() as db:
        yield db


def get_store() -> VectorStore:
    return get_vector_store()


def get_embed() -> Callable[[list[str]], list[list[float]]]:
    return provider_embed


def get_generate() -> Callable[..., str]:
    return provider_generate


# --- helpers -----------------------------------------------------------------

def cite(hits: list[Hit]) -> list[Citation]:
    """D7: one citation per document and section, keeping the highest score."""
    best: dict[tuple[str, str], Citation] = {}
    for hit in hits:
        key = (hit.document_id, hit.section)
        citation = Citation(
            document_id=hit.document_id,
            document_title=hit.document_title,
            section=hit.section,
            version=str(hit.metadata.get("version", "")),
            status=hit.metadata.get("status", "current"),
            score=hit.score,
        )
        if key not in best or citation.score > best[key].score:
            best[key] = citation
    return sorted(best.values(), key=lambda c: c.score, reverse=True)


def _conversation(db: Session, conversation_id: str | None) -> Conversation:
    if conversation_id is None:
        conversation = Conversation()
        db.add(conversation)
        db.flush()
        return conversation
    try:
        parsed = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="conversation not found") from None
    conversation = db.get(Conversation, parsed)
    if conversation is None:
        raise HTTPException(status_code=404, detail="conversation not found")
    return conversation


# --- the endpoint ------------------------------------------------------------

@router.post("/ask", response_model=AskResponse)
def ask(
    body: AskRequest,
    db: Session = Depends(get_db),
    store: VectorStore = Depends(get_store),
    embed: Callable[[list[str]], list[list[float]]] = Depends(get_embed),
    generate: Callable[..., str] = Depends(get_generate),
) -> AskResponse:
    conversation = _conversation(db, body.conversation_id)
    db.add(Message(conversation_id=conversation.id, role="user", content=body.question))

    try:
        retrieval = retrieve_grounded(body.question, store, embed)
    except ProviderError as error:
        # No question embedding means no search: this is neither an answer nor
        # a refusal. The turn is not stored (the session rolls back), and the
        # client sees an error rather than a made-up outcome.
        raise HTTPException(
            status_code=503,
            detail="The model provider is unreachable, so the question could not be searched.",
        ) from error

    if isinstance(retrieval, Grounded):
        composition = compose(body.question, retrieval, generate)
        if isinstance(composition, Answered):
            outcome, answer = "answered", composition.text
            hits, latency_ms = composition.hits, composition.latency_ms
            prompt_version, model, notice = composition.prompt_version, composition.model, composition.notice
        else:
            outcome, answer, hits = "degraded", None, composition.hits
            latency_ms, prompt_version, model, notice = 0, None, None, composition.reason
    else:
        outcome, answer, hits = "refused", retrieval.reason, []
        latency_ms, prompt_version, model, notice = 0, None, None, None

    citations = cite(hits)
    assistant = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        outcome=outcome,
        model=model,
        prompt_version=prompt_version,
        latency_ms=latency_ms,
    )
    assistant.citations = [
        MessageCitation(
            document_id=c.document_id,
            document_title=c.document_title,
            section=c.section,
            version=c.version,
            status=c.status,
            score=c.score,
        )
        for c in citations
    ]
    db.add(assistant)
    db.flush()

    return AskResponse(
        outcome=outcome,
        answer=answer,
        citations=citations,
        conversation_id=str(conversation.id),
        message_id=str(assistant.id),
        latency_ms=latency_ms,
        notice=notice if outcome != "refused" else None,
    )
