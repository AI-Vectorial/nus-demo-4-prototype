"""F8 -- history. REQ-C8, REQ-C9, REQ-A6, REQ-U13, REQ-U14.

A conversation is listed only once it has a turn (REQ-U14). Its title is the
first question, truncated. There is no separate title column (features.md).
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.records import Conversation, Message

TITLE_LENGTH = 80


def _title(db: Session, conversation_id: uuid.UUID) -> str:
    first = db.scalars(
        select(Message.content)
        .where(Message.conversation_id == conversation_id, Message.role == "user")
        .order_by(Message.created_at.asc())
        .limit(1)
    ).first()
    text = (first or "").strip()
    return text if len(text) <= TITLE_LENGTH else text[: TITLE_LENGTH - 1].rstrip() + "…"


def list_conversations(db: Session, limit: int, offset: int) -> list[dict]:
    counts = (
        select(Message.conversation_id, func.count(Message.id).label("n"))
        .group_by(Message.conversation_id)
        .subquery()
    )
    rows = db.execute(
        select(Conversation, counts.c.n)
        .join(counts, counts.c.conversation_id == Conversation.id)
        .order_by(Conversation.last_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return [
        {
            "id": conversation.id,
            "started_at": conversation.started_at,
            "last_at": conversation.last_at,
            "title": _title(db, conversation.id),
            "message_count": int(n),
        }
        for conversation, n in rows
    ]


def get_conversation(db: Session, conversation_id: uuid.UUID) -> dict | None:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        return None
    messages = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    ).all()
    return {
        "id": conversation.id,
        "started_at": conversation.started_at,
        "last_at": conversation.last_at,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "outcome": m.outcome,
                "created_at": m.created_at,
                "citations": [
                    {
                        "document_id": c.document_id,
                        "document_title": c.document_title,
                        "section": c.section,
                        "version": c.version,
                        "status": c.status,
                        "score": round(c.score, 4),
                    }
                    for c in m.citations
                ],
            }
            for m in messages
        ],
    }
