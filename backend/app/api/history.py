from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, exists, func, select
from sqlalchemy.orm import Session, selectinload

from app.api.ask import CitationResponse
from app.core.database import get_session
from app.core.models import Conversation, Message

router = APIRouter(tags=["history"])


class ConversationSummary(BaseModel):
    id: UUID
    started_at: datetime
    last_at: datetime
    preview: str
    turns: int


class ConversationPage(BaseModel):
    conversations: list[ConversationSummary]
    total: int
    limit: int
    offset: int


class ConversationMessage(BaseModel):
    id: UUID
    role: Literal["user", "assistant"]
    content: str | None
    outcome: Literal["answered", "refused", "degraded"] | None
    created_at: datetime
    citations: list[CitationResponse]


class ConversationDetail(BaseModel):
    id: UUID
    started_at: datetime
    last_at: datetime
    messages: list[ConversationMessage]


def _has_turns():
    has_user = exists(
        select(Message.id).where(
            Message.conversation_id == Conversation.id,
            Message.role == "user",
        )
    )
    has_assistant = exists(
        select(Message.id).where(
            Message.conversation_id == Conversation.id,
            Message.role == "assistant",
        )
    )
    return and_(has_user, has_assistant)


@router.get("/conversations", response_model=ConversationPage)
def list_conversations(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ConversationPage:
    eligible = _has_turns()
    total = session.scalar(
        select(func.count(Conversation.id)).where(eligible)
    ) or 0
    first_question = (
        select(Message.content)
        .where(
            Message.conversation_id == Conversation.id,
            Message.role == "user",
        )
        .order_by(Message.created_at, Message.id)
        .limit(1)
        .scalar_subquery()
    )
    turn_count = (
        select(func.count(Message.id))
        .where(
            Message.conversation_id == Conversation.id,
            Message.role == "assistant",
        )
        .scalar_subquery()
    )
    rows = session.execute(
        select(Conversation, first_question, turn_count)
        .where(eligible)
        .order_by(Conversation.last_at.desc(), Conversation.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    summaries = [
        ConversationSummary(
            id=conversation.id,
            started_at=conversation.started_at,
            last_at=conversation.last_at,
            preview=preview or "",
            turns=turns,
        )
        for conversation, preview, turns in rows
    ]
    return ConversationPage(
        conversations=summaries,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: UUID,
    session: Annotated[Session, Depends(get_session)],
) -> ConversationDetail:
    conversation = session.scalar(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(
            selectinload(Conversation.messages).selectinload(Message.citations)
        )
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = sorted(
        conversation.messages,
        key=lambda message: (message.created_at, str(message.id)),
    )
    return ConversationDetail(
        id=conversation.id,
        started_at=conversation.started_at,
        last_at=conversation.last_at,
        messages=[
            ConversationMessage(
                id=message.id,
                role=message.role,
                content=message.content,
                outcome=message.outcome,
                created_at=message.created_at,
                citations=[
                    CitationResponse(
                        document_id=citation.document_id,
                        document_title=citation.document_title,
                        section=citation.section,
                        version=citation.version,
                        status=citation.status,
                        score=citation.score,
                    )
                    for citation in message.citations
                ],
            )
            for message in messages
        ],
    )
