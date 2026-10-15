"""Response shapes, from PRD section 5. Fixed: add fields if needed, do not rename."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    conversation_id: uuid.UUID | None = None

    @field_validator("question")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be blank")
        return value


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
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    latency_ms: int


class ConversationSummary(BaseModel):
    id: uuid.UUID
    started_at: datetime
    last_at: datetime
    title: str
    message_count: int


class MessageView(BaseModel):
    id: uuid.UUID
    role: str
    content: str | None
    outcome: str | None
    created_at: datetime
    citations: list[Citation]


class ConversationView(BaseModel):
    id: uuid.UUID
    started_at: datetime
    last_at: datetime
    messages: list[MessageView]


class Section(BaseModel):
    heading: str
    text: str


class DocumentSummary(BaseModel):
    id: str
    title: str
    owner: str
    version: str
    effective: str
    status: Literal["current", "superseded"]
    sections: list[Section]
