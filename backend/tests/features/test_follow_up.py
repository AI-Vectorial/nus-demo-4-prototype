from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.models import Conversation, Message
from app.features.answer import Answered
from app.features.ask import ask_policy
from app.retrieve.query import Grounded


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_sessions = sessionmaker(bind=engine, expire_on_commit=False)
    with test_sessions() as session:
        yield session
    engine.dispose()


def test_follow_up_retrieves_with_recent_user_questions_and_answer_context(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    conversation = Conversation()
    db_session.add(conversation)
    db_session.flush()
    start = datetime.now(UTC) - timedelta(minutes=10)
    for index in range(6):
        created_at = start + timedelta(minutes=index)
        db_session.add_all(
            [
                Message(
                    conversation_id=conversation.id,
                    role="user",
                    content=f"question {index}",
                    created_at=created_at,
                ),
                Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=f"answer {index}",
                    created_at=created_at + timedelta(seconds=1),
                    outcome="answered",
                ),
            ]
        )
    db_session.flush()

    retrieval_queries: list[str] = []
    generation_contexts: list[str] = []

    def retrieve_again(query: str) -> Grounded:
        retrieval_queries.append(query)
        return Grounded(hits=[])

    def generate_with_context(
        question: str, hits, *, conversation_context: str = ""
    ) -> Answered:
        generation_contexts.append(conversation_context)
        return Answered(
            answer="The current policy applies.",
            citations=[],
            model="test-model",
            prompt_version="v1",
            latency_ms=0,
        )

    monkeypatch.setattr("app.features.ask.retrieve", retrieve_again)
    monkeypatch.setattr(
        "app.features.ask.generate_answer", generate_with_context
    )

    response = ask_policy(db_session, "And above £500?", conversation.id)

    assert response["outcome"] == "answered"
    assert len(retrieval_queries) == 1
    assert "question 0" not in retrieval_queries[0]
    assert all(f"question {index}" in retrieval_queries[0] for index in range(1, 6))
    assert "answer " not in retrieval_queries[0]
    assert "And above £500?" in retrieval_queries[0]
    assert "question 0" not in generation_contexts[0]
    assert all(f"question {index}" in generation_contexts[0] for index in range(1, 6))
    assert all(f"answer {index}" in generation_contexts[0] for index in range(1, 6))


def test_new_conversation_starts_without_previous_context(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    retrieval_queries: list[str] = []
    generation_contexts: list[str] = []

    def retrieve_again(query: str) -> Grounded:
        retrieval_queries.append(query)
        return Grounded(hits=[])

    def generate_without_context(
        question: str, hits, *, conversation_context: str = ""
    ) -> Answered:
        generation_contexts.append(conversation_context)
        return Answered(
            answer="A new conversation answer.",
            citations=[],
            model="test-model",
            prompt_version="v1",
            latency_ms=0,
        )

    monkeypatch.setattr("app.features.ask.retrieve", retrieve_again)
    monkeypatch.setattr("app.features.ask.generate_answer", generate_without_context)

    first = ask_policy(db_session, "First conversation question", None)
    second = ask_policy(db_session, "Question after Reset", None)

    assert UUID(str(first["conversation_id"])) != UUID(str(second["conversation_id"]))
    assert retrieval_queries == [
        "First conversation question",
        "Question after Reset",
    ]
    assert generation_contexts == ["", ""]
