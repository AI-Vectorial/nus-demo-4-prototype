"""GET /conversations and GET /conversations/{id} -- history (F8).

A conversation's title is its first question, truncated: derived, so there is
no second copy to keep in step. A conversation with no turns is never listed
(REQ-U14).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.ask import Citation
from app.core.database import get_session
from app.core.models import Conversation, Message

router = APIRouter(tags=["conversations"])

TITLE_LENGTH = 80


class ConversationSummary(BaseModel):
    id: uuid.UUID
    started_at: datetime
    last_at: datetime
    title: str
    message_count: int


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str | None
    outcome: str | None
    citations: list[Citation]
    latency_ms: int | None
    created_at: datetime


class ConversationOut(BaseModel):
    id: uuid.UUID
    started_at: datetime
    last_at: datetime
    messages: list[MessageOut]


def _title(question: str) -> str:
    return question if len(question) <= TITLE_LENGTH else question[:TITLE_LENGTH].rstrip() + "…"


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(
    db: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ConversationSummary]:
    counts = (select(Message.conversation_id, func.count().label("n"))
              .group_by(Message.conversation_id).subquery())
    first_question = (
        select(Message.content)
        .where(Message.conversation_id == Conversation.id, Message.role == "user")
        .order_by(Message.created_at).limit(1)
        .correlate(Conversation).scalar_subquery()
    )
    rows = db.execute(
        select(Conversation, counts.c.n, first_question)
        .join(counts, counts.c.conversation_id == Conversation.id)
        .order_by(Conversation.last_at.desc())
        .limit(limit).offset(offset)
    ).all()
    return [
        ConversationSummary(id=c.id, started_at=c.started_at, last_at=c.last_at,
                            title=_title(first or ""), message_count=n)
        for c, n, first in rows
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation(conversation_id: uuid.UUID,
                     db: Annotated[Session, Depends(get_session)]) -> ConversationOut:
    conversation = db.scalar(
        select(Conversation).where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages).selectinload(Message.citations))
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="conversation not found")
    return ConversationOut(
        id=conversation.id,
        started_at=conversation.started_at,
        last_at=conversation.last_at,
        messages=[
            MessageOut(
                id=m.id, role=m.role, content=m.content, outcome=m.outcome,
                latency_ms=m.latency_ms, created_at=m.created_at,
                citations=[Citation(document_id=c.document_id, document_title=c.document_title,
                                    section=c.section, version=c.version, status=c.status,
                                    score=c.score) for c in m.citations],
            )
            for m in conversation.messages
        ],
    )
