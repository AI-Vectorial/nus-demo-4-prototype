"""One question, one of three outcomes, one recorded turn.

    question ─▶ retrieve ─▶ Insufficient ─▶ refused    (no model call)
                        └─▶ Grounded ─────▶ compose ─▶ answered | degraded

The turn -- the question and the outcome -- is written once the outcome is
known, in the same transaction, for all three outcomes. A refusal is recorded
as carefully as an answer: it is the behaviour the product is judged on.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.models import Conversation, Message, MessageCitation
from app.features.refusal import refusal_message
from app.generate.answer import Answered, compose
from app.retrieve.retrieve import Embed, Insufficient, retrieve
from app.retrieve.store import Hit, VectorStore


class ConversationNotFound(LookupError):
    pass


@dataclass(frozen=True)
class Citation:
    document_id: str
    document_title: str
    section: str
    version: str
    status: str
    score: float


@dataclass(frozen=True)
class Outcome:
    outcome: str
    answer: str | None
    citations: list[Citation]
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    latency_ms: int


def citations(hits: tuple[Hit, ...]) -> list[Citation]:
    """One citation per document version and section, highest score kept. D7."""
    best: dict[tuple[str, str, str], Citation] = {}
    for hit in hits:
        citation = Citation(
            document_id=hit.document_id,
            document_title=hit.document_title,
            section=hit.section,
            version=str(hit.metadata.get("version", "")),
            status=str(hit.metadata.get("status", "current")),
            score=hit.score,
        )
        key = (citation.document_id, citation.version, citation.section)
        if key not in best or citation.score > best[key].score:
            best[key] = citation
    return sorted(best.values(), key=lambda c: c.score, reverse=True)


def ask(
    question: str,
    conversation_id: uuid.UUID | None,
    *,
    db: Session,
    store: VectorStore,
    embed: Embed,
    generate: Callable[..., str],
    top_k: int,
    min_score: float,
    model_name: str,
    generation_enabled: bool,
    corpus_dir: Path,
) -> Outcome:
    started = time.monotonic()

    conversation = _conversation(db, conversation_id)
    result = retrieve(question, store=store, embed=embed, top_k=top_k, min_score=min_score)

    model = prompt_version = None
    if isinstance(result, Insufficient):
        outcome, answer, cited = "refused", refusal_message(result, corpus_dir), []
    else:
        composed = compose(question, result, generate=generate, model_name=model_name,
                           enabled=generation_enabled)
        cited = citations(composed.hits)
        if isinstance(composed, Answered):
            outcome, answer = "answered", composed.text
            model, prompt_version = composed.model, composed.prompt_version
        else:
            outcome, answer = "degraded", None

    latency_ms = int((time.monotonic() - started) * 1000)
    reply = _record(db, conversation, question, outcome=outcome, answer=answer, cited=cited,
                    model=model, prompt_version=prompt_version, latency_ms=latency_ms)
    return Outcome(outcome, answer, cited, conversation.id, reply.id, latency_ms)


def _conversation(db: Session, conversation_id: uuid.UUID | None) -> Conversation:
    if conversation_id is None:
        conversation = Conversation(id=uuid.uuid4())
        db.add(conversation)
        return conversation
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise ConversationNotFound(str(conversation_id))
    return conversation


def _record(
    db: Session,
    conversation: Conversation,
    question: str,
    *,
    outcome: str,
    answer: str | None,
    cited: list[Citation],
    model: str | None,
    prompt_version: str | None,
    latency_ms: int,
) -> Message:
    now = datetime.now(UTC)
    db.add(Message(conversation_id=conversation.id, role="user", content=question,
                   created_at=now))
    reply = Message(
        id=uuid.uuid4(),
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        outcome=outcome,
        model=model,
        prompt_version=prompt_version,
        latency_ms=latency_ms,
        created_at=now,
        citations=[MessageCitation(**vars(c)) for c in cited],
    )
    db.add(reply)
    conversation.last_at = now
    db.flush()
    return reply
