"""The wire contract -- PRD section 5, fixed.

These are the shapes five tables build against and `ci/` tests, so nothing here
is renamed for convenience. Where the PRD shows a field, it is here with that
name, and where it shows three outcomes they are a Literal rather than a str --
a client must never have to deduce a refusal from a null answer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Outcome = Literal["answered", "refused", "degraded"]


class CitationOut(BaseModel):
    """One passage an answer was built from. Built from the payload in PRD 7."""

    document_id: str
    document_title: str
    section: str
    version: str
    status: str
    score: float

    model_config = ConfigDict(from_attributes=True)


class AskRequest(BaseModel):
    """conversation_id is null on the first question and the id thereafter."""

    question: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = None


class AskResponse(BaseModel):
    """answered: text + the passages used. refused: the reason, and no
    passages. degraded: no text, and the passages that were found."""

    outcome: Outcome
    answer: str | None
    citations: list[CitationOut]
    conversation_id: str
    message_id: str
    latency_ms: int


class MessageOut(BaseModel):
    """One stored turn. The assistant-only fields are null on a question."""

    id: str
    role: str
    content: str | None
    outcome: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    latency_ms: int | None = None
    created_at: datetime
    citations: list[CitationOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ConversationOut(BaseModel):
    """A conversation and its turns -- REQ-A3."""

    id: str
    started_at: datetime
    last_at: datetime
    messages: list[MessageOut]

    model_config = ConfigDict(from_attributes=True)


class ConversationSummaryOut(BaseModel):
    """One row of GET /conversations -- REQ-A6, REQ-C8.

    `title` is derived from the first user message, never stored. A title
    column would be a second source of truth to keep in step with the
    conversation, for no gain -- the first question is already the thing a
    reader recognises the thread by.
    """

    id: str
    started_at: datetime
    last_at: datetime
    title: str
    message_count: int


class CorpusSectionOut(BaseModel):
    """A section of a policy document, and its text."""

    heading: str
    text: str


class CorpusDocumentOut(BaseModel):
    """A document in the list at /corpus -- headings only, no body.

    status is what REQ-B2 hangs on: a superseded document is listed, not
    hidden, so that "is this still current?" stays answerable.
    """

    id: str
    title: str
    owner: str
    version: str
    effective: str
    status: str
    sections: list[str]


class CorpusDocumentDetailOut(BaseModel):
    """One document at /corpus/{id}, with the text of every section."""

    id: str
    title: str
    owner: str
    version: str
    effective: str
    status: str
    sections: list[CorpusSectionOut]
