"""The record of every exchange -- PRD section 6, fixed.

Ids are uuid strings rather than a native uuid column. pg8000 is the driver
(psycopg is LGPLv3 and CI refused it), and a text id behaves identically on
Postgres and on whatever a test spins up in memory -- one less thing that is
only true in production.

`messages` is both the record and the context: the last CONTEXT_MESSAGES rows
of a conversation are what a follow-up is answered with, so the thing an
auditor reads is the same thing the model read.
"""

from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

_clock_lock = threading.Lock()
_last_issued: datetime | None = None


def new_id() -> str:
    """A uuid string, generated here rather than by the database.

    /ask must be able to return a message_id even when the write behind it
    failed -- losing the answer because the record could not be stored is the
    worse of the two outcomes.
    """
    return str(uuid.uuid4())


def now() -> datetime:
    """The wall clock, forced strictly increasing within this process.

    Conversations are reconstructed by ordering on created_at, and Windows
    ticks its clock roughly every 15ms -- long enough for a question and its
    answer to share a timestamp and come back in the wrong order. Nudging
    forward by a microsecond keeps the ordering honest without adding a
    sequence column the fixed data model does not have.
    """
    global _last_issued
    with _clock_lock:
        moment = datetime.now(UTC)
        if _last_issued is not None and moment <= _last_issued:
            moment = _last_issued + timedelta(microseconds=1)
        _last_issued = moment
        return moment


class Conversation(Base):
    """One thread of questions. Created on the first question (REQ-C1)."""

    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=now
    )
    last_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=now
    )

    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
        lazy="selectin",
    )


class Message(Base):
    """One turn -- a question, or the answer to one (REQ-C2)."""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Assistant turns only: answered | refused | degraded. Explicit, never
    # inferred from a null answer.
    outcome: Mapped[str | None] = mapped_column(String(16), nullable=True)

    # REQ-G5: what produced this answer, so it can be reproduced or blamed.
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=now
    )

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    citations: Mapped[list[MessageCitation]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class MessageCitation(Base):
    """A passage an answer was built from, with the policy version it came from.

    Stored rather than recomputed: policy changes, and an audit of what was
    said in March must show the version that was current in March.
    """

    __tablename__ = "message_citations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    message_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[str] = mapped_column(String(128), nullable=False)
    document_title: Mapped[str] = mapped_column(String(256), nullable=False)
    section: Mapped[str] = mapped_column(String(256), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)

    message: Mapped[Message] = relationship(back_populates="citations")
