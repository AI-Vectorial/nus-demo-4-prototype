from __future__ import annotations

import time
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.models import Conversation, Message, MessageCitation
from app.features.answer import Degraded, generate_answer
from app.retrieve.query import Grounded, Insufficient, retrieve
from app.retrieve.store import Hit

REFUSAL_MESSAGE = (
    "I can’t find enough support for an answer in the indexed policy. "
    "Please contact Compliance."
)


def _group_citations(hits: list[Hit]) -> list[Hit]:
    grouped: dict[tuple[str, str, str], Hit] = {}
    for hit in hits:
        key = (hit.document_id, hit.section, str(hit.metadata.get("version", "")))
        existing = grouped.get(key)
        if existing is None or hit.score > existing.score:
            grouped[key] = hit
    return list(grouped.values())


def ask_policy(
    session: Session,
    question: str,
    conversation_id: UUID | None,
) -> dict[str, object]:
    started = time.perf_counter()
    if conversation_id is None:
        conversation = Conversation()
        session.add(conversation)
        session.flush()
    else:
        conversation = session.get(Conversation, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")

    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=question,
    )
    session.add(user_message)
    session.flush()

    result = retrieve(question)
    if isinstance(result, Insufficient):
        outcome = "refused"
        answer: str | None = REFUSAL_MESSAGE
        hits: list[Hit] = []
        model_name = None
        prompt_version = None
    elif isinstance(result, Grounded):
        generated = generate_answer(question, result.hits)
        hits = _group_citations(generated.citations)
        if isinstance(generated, Degraded):
            outcome = "degraded"
            answer = None
        else:
            outcome = "answered"
            answer = generated.answer
        model_name = generated.model
        prompt_version = generated.prompt_version
    else:
        raise TypeError(f"Unsupported retrieval result: {type(result).__name__}")

    latency_ms = int((time.perf_counter() - started) * 1000)
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        outcome=outcome,
        model=model_name,
        prompt_version=prompt_version,
        latency_ms=latency_ms,
    )
    assistant_message.citations = [
        MessageCitation(
            document_id=hit.document_id,
            document_title=hit.document_title,
            section=hit.section,
            version=str(hit.metadata.get("version", "")),
            status=str(hit.metadata.get("status", "current")),
            score=hit.score,
        )
        for hit in hits
    ]
    session.add(assistant_message)
    conversation.last_at = datetime.now(UTC)
    session.flush()

    return {
        "outcome": outcome,
        "answer": answer,
        "citations": [
            {
                "document_id": hit.document_id,
                "document_title": hit.document_title,
                "section": hit.section,
                "version": str(hit.metadata.get("version", "")),
                "status": str(hit.metadata.get("status", "current")),
                "score": hit.score,
            }
            for hit in hits
        ],
        "conversation_id": str(conversation.id),
        "message_id": str(assistant_message.id),
        "latency_ms": latency_ms,
    }
