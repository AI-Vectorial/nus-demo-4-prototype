"""POST /ask -- the endpoint that makes this a product.

The order of the turn is deliberate:

    conversation -> store the question -> RETRIEVE -> answer or refuse ->
    store the answer -> respond

Retrieval sits before the fork, and the fork is on a *type* rather than an
empty list, so the model is never asked whether it knows something. The
refusal path makes no model call at all, which is why a refusal is visibly
faster than an answer (NFR-2).

Persistence is best-effort on purpose. The user's answer has already been
composed by the time it is written down; losing it because Postgres blinked
would turn a storage problem into a product failure.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import AskRequest, AskResponse, CitationOut, ConversationOut
from app.core.config import settings
from app.core.database import session_scope
from app.core.models import Conversation, Message, MessageCitation, new_id, now
from app.retrieve.store import Hit

log = logging.getLogger(__name__)

router = APIRouter(tags=["ask"])


@dataclass
class _Turn:
    """What the question half of a turn leaves behind for the answer half."""

    conversation_id: str
    history: list[tuple[str, str]] = field(default_factory=list)
    recorded: bool = False


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    """Answer a policy question, or refuse it -- REQ-A1."""
    # Imported at call time, not at module scope. Retrieval reaches Qdrant and
    # generation reaches OpenRouter; binding either at import would make an
    # unreachable dependency a boot failure rather than something /healthz
    # reports (NFR-5).
    from app.generate.service import answer
    from app.retrieve.service import Insufficient, retrieve

    started = time.perf_counter()
    turn = _open_turn(payload)

    # REQ-C5 / D9: retrieval runs on EVERY turn, follow-up included. "And what
    # about above 500?" needs a different row of the same table; reusing the
    # previous turn's passages gives a confident answer from the wrong section,
    # and it still looks right.
    #
    # The history goes in because a follow-up on its own carries no policy
    # vocabulary -- embedded alone it matches nothing and is refused. Retrieval
    # runs on the conversation; the answer is composed for the question asked.
    result = retrieve(payload.question, turn.history or None)

    model: str | None = None
    prompt_version: str | None = None

    if isinstance(result, Insufficient):
        outcome = "refused"
        text: str | None = _refusal(result.reason, result.owner_hint)
        citations: list[CitationOut] = []
        recorded_latency: int | None = None
    else:
        composed = answer(result, turn.history or None)
        outcome = "degraded" if composed.degraded else "answered"
        text = composed.text
        citations = _citations(result.passages)
        model = composed.model
        prompt_version = composed.prompt_version
        recorded_latency = composed.latency_ms

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    message_id = new_id()

    _close_turn(
        turn,
        message_id=message_id,
        outcome=outcome,
        content=text,
        citations=citations,
        model=model,
        prompt_version=prompt_version,
        # REQ-G5 stores what the model call cost; the response reports what the
        # caller waited for. They are different numbers and both are wanted.
        latency_ms=recorded_latency if recorded_latency is not None else elapsed_ms,
    )

    return AskResponse(
        outcome=outcome,
        answer=text,
        citations=citations,
        conversation_id=turn.conversation_id,
        message_id=message_id,
        latency_ms=elapsed_ms,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation(conversation_id: str) -> ConversationOut:
    """A conversation and its turns -- REQ-A3."""
    with session_scope() as db:
        conversation = db.get(Conversation, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="conversation not found")
        # Built inside the session: the messages and their citations are loaded
        # while there is still a connection to load them with.
        return ConversationOut.model_validate(conversation)


# --- the two halves of a turn ---------------------------------------------


def _open_turn(payload: AskRequest) -> _Turn:
    """Find or start the conversation, store the question, read the context.

    Never raises. A database that is down costs the user their history, which
    is recoverable; it must not cost them their answer, which is not.
    """
    try:
        with session_scope() as db:
            conversation = _conversation(db, payload.conversation_id)
            db.add(
                Message(
                    conversation_id=conversation.id,
                    role="user",
                    content=payload.question,
                    created_at=now(),
                )
            )
            db.flush()
            return _Turn(conversation.id, _history(db, conversation.id), recorded=True)
    except Exception:  # noqa: BLE001 - degraded, logged, and reported as such
        log.exception("could not open the turn; answering without stored context")
        return _Turn(payload.conversation_id or new_id())


def _close_turn(
    turn: _Turn,
    *,
    message_id: str,
    outcome: str,
    content: str | None,
    citations: list[CitationOut],
    model: str | None,
    prompt_version: str | None,
    latency_ms: int,
) -> None:
    """Store the assistant turn and its citations. Never raises -- see above."""
    if not turn.recorded:
        return  # the question was never stored; there is nothing to attach to
    try:
        with session_scope() as db:
            conversation = db.get(Conversation, turn.conversation_id)
            if conversation is None:
                return
            db.add(
                Message(
                    id=message_id,
                    conversation_id=turn.conversation_id,
                    role="assistant",
                    content=content,
                    outcome=outcome,
                    model=model,
                    prompt_version=prompt_version,
                    latency_ms=latency_ms,
                    created_at=now(),
                )
            )
            db.add_all(
                MessageCitation(message_id=message_id, **citation.model_dump())
                for citation in citations
            )
            conversation.last_at = now()
    except Exception:  # noqa: BLE001 - degraded, logged, and reported as such
        log.exception("could not store the answer for conversation %s", turn.conversation_id)


def _conversation(db: Session, conversation_id: str | None) -> Conversation:
    """The conversation this question belongs to -- REQ-C1.

    An id we have never seen starts a fresh conversation rather than 404ing:
    the client's copy can outlive a database reset, and the response carries
    the id to use from then on.
    """
    if conversation_id:
        existing = db.get(Conversation, conversation_id)
        if existing is not None:
            return existing
    conversation = Conversation(id=new_id(), started_at=now(), last_at=now())
    db.add(conversation)
    db.flush()
    return conversation


def _history(db: Session, conversation_id: str) -> list[tuple[str, str]]:
    """The last CONTEXT_MESSAGES turns, oldest first -- REQ-C3, REQ-C4, D8.

    Five is enough for "and what about above 500?" to resolve and few enough
    that an older topic does not drag the answer off course. The question just
    stored is the last entry, so generation sees the thread as it happened.
    """
    rows = db.execute(
        select(Message.role, Message.content)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(settings.context_messages)
    ).all()
    return [(role, content or "") for role, content in reversed(rows)]


# --- the two shapes an outcome takes ---------------------------------------


def _citations(passages: list[Hit]) -> list[CitationOut]:
    """One citation per section, best score wins -- D7.

    Two passages from section 4.2 are one citation. Grouping by document
    instead would lose the section, which is the part a human can check.
    """
    seen: dict[tuple[str, str, str], CitationOut] = {}
    for hit in passages:  # already best first
        metadata = hit.metadata or {}
        version = str(metadata.get("version", ""))
        key = (hit.document_id, version, hit.section)
        if key in seen:
            continue
        seen[key] = CitationOut(
            document_id=hit.document_id,
            document_title=hit.document_title,
            section=hit.section,
            version=version,
            status=str(metadata.get("status", "current")),
            score=hit.score,
        )
    return list(seen.values())


def _refusal(reason: str, owner_hint: str | None) -> str:
    """What a refusal says -- D5.

    "I don't know" leaves the user exactly where they started. Every policy
    document names an owner in its front matter, so a refusal can name a real
    team to ask instead.
    """
    parts = ["I could not find anything in Aldermere's policy corpus that answers this."]
    if reason:
        parts.append(reason)
    if owner_hint:
        parts.append(
            f"{owner_hint} owns the closest policy and can tell you whether a rule exists."
        )
    else:
        parts.append(
            "The Policy Office can tell you whether a rule exists outside the published corpus."
        )
    parts.append("I have not guessed an answer, because a wrong one here is worse than none.")
    return " ".join(parts)
