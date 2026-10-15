"""F5 + F6 -- ask a question, record the exchange, and answer follow-ups.

One exchange:
  1. Load the conversation, or start one (REQ-C1).
  2. Build the retrieval query from the conversation's recent user turns, latest
     last (D9, REQ-C7). Retrieval always runs (REQ-C5).
  3. Ground it (F3). Nothing above MIN_SCORE: refuse, and make no model call.
  4. Compose from the passages (F4), passing recent questions as context (REQ-C3).
     If the model is off or unreachable: degraded, with the passages and no answer.
  5. Record the user turn and the assistant turn, with citations (REQ-C2, REQ-G5).

Citations are one per section (D7). Superseded status is carried on each one (REQ-U4).
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.records import Conversation, Message, MessageCitation
from app.generate import ProviderError, embed
from app.generate.client import time_budget
from app.generate.compose import PROMPT_VERSION, compose_answer
from app.retrieve import get_vector_store
from app.retrieve.ground import Insufficient, ground
from app.retrieve.store import Hit, RetrievalUnavailable


class ConversationNotFound(LookupError):
    pass


class SearchUnavailable(RuntimeError):
    """Retrieval could not run. Nothing is recorded and nothing is answered (review F1)."""


@dataclass(frozen=True)
class Exchange:
    outcome: str
    answer: str | None
    citations: list[dict]
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    latency_ms: int


def _now() -> datetime:
    return datetime.now(UTC)


def _load_or_start(db: Session, conversation_id: uuid.UUID | None) -> Conversation:
    if conversation_id is None:
        # The id is set here, not left to the database, because the turns that
        # belong to this conversation are created before anything is flushed.
        conversation = Conversation(id=uuid.uuid4(), started_at=_now(), last_at=_now())
        db.add(conversation)
        return conversation
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise ConversationNotFound(str(conversation_id))
    return conversation


def _recent_messages(db: Session, conversation_id: uuid.UUID, count: int) -> list[Message]:
    """The last `count` rows of the conversation, oldest first (REQ-C4)."""
    if count <= 0:
        return []
    rows = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(count)
    ).all()
    return list(reversed(rows))


def citations_for(hits: list[Hit]) -> list[dict]:
    """One citation per section (D7). Keeps the best score seen for each section."""
    grouped: dict[tuple[str, str, str], dict] = {}
    for hit in hits:
        version = str(hit.metadata.get("version", ""))
        key = (hit.document_id, version, hit.section)
        if key not in grouped or hit.score > grouped[key]["score"]:
            grouped[key] = {
                "document_id": hit.document_id,
                "document_title": hit.document_title,
                "section": hit.section,
                "version": version,
                "status": str(hit.metadata.get("status", "current")),
                "score": round(float(hit.score), 4),
            }
    return list(grouped.values())


def answer(
    db: Session,
    question: str,
    conversation_id: uuid.UUID | None = None,
) -> Exchange:
    # One budget for the whole answer (review F12). Embedding, search and
    # composition all draw on it, so the total stays under the gateway limit.
    with time_budget(settings.answer_budget_seconds):
        return _answer(db, question, conversation_id)


def _answer(
    db: Session,
    question: str,
    conversation_id: uuid.UUID | None,
) -> Exchange:
    started = time.perf_counter()
    question = question.strip()

    conversation = _load_or_start(db, conversation_id)
    context = _recent_messages(db, conversation.id, settings.context_messages)
    earlier = [m.content for m in context if m.role == "user" and m.content]

    # D9: retrieval runs on the conversation's user turns, latest last.
    query = "\n".join([*earlier, question])

    user_turn = Message(
        conversation_id=conversation.id, role="user", content=question, created_at=_now()
    )
    db.add(user_turn)

    try:
        result = ground(get_vector_store(), embed, query)
    except (ProviderError, RetrievalUnavailable) as error:
        # Roll back the pending conversation and user turn, so a failed search
        # leaves no record behind (review F1).
        db.rollback()
        raise SearchUnavailable(type(error).__name__) from error

    model: str | None = None
    prompt_version: str | None = None
    if isinstance(result, Insufficient):
        outcome, text, cited = "refused", result.reason, []
    else:
        cited = citations_for(result.passages)
        if not settings.generation_enabled:
            outcome, text = "degraded", None
        else:
            model, prompt_version = settings.llm_model, PROMPT_VERSION
            try:
                text = compose_answer(question, result.passages, earlier)
                outcome = "answered"
            except ProviderError:
                outcome, text = "degraded", None

    latency_ms = int((time.perf_counter() - started) * 1000)
    assistant_turn = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=text,
        outcome=outcome,
        model=model,
        prompt_version=prompt_version,
        latency_ms=latency_ms,
        created_at=_now(),
    )
    assistant_turn.citations = [
        MessageCitation(position=i, **c) for i, c in enumerate(cited)
    ]
    db.add(assistant_turn)
    conversation.last_at = _now()
    db.flush()

    return Exchange(
        outcome=outcome,
        answer=text,
        citations=cited,
        conversation_id=conversation.id,
        message_id=assistant_turn.id,
        latency_ms=latency_ms,
    )
