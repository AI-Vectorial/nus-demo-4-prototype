from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_session
from app.core.models import Conversation, Message, MessageCitation
from app.main import app


@pytest.fixture
def history_client() -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_sessions = sessionmaker(bind=engine, expire_on_commit=False)

    def override_session() -> Iterator[Session]:
        with test_sessions() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    app.dependency_overrides[get_session] = override_session
    yield TestClient(app), test_sessions
    app.dependency_overrides.clear()
    engine.dispose()


def seed_conversation(
    session: Session, *, title: str, last_at: datetime, with_turn: bool = True
) -> UUID:
    conversation = Conversation(
        started_at=last_at - timedelta(minutes=5),
        last_at=last_at,
    )
    session.add(conversation)
    session.flush()
    if with_turn:
        asked_at = last_at - timedelta(seconds=2)
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=title,
            created_at=asked_at,
        )
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=f"Answer to {title}",
            outcome="answered",
            created_at=last_at,
        )
        assistant_message.citations = [
            MessageCitation(
                document_id="travel-expense-policy",
                document_title="Travel and Expense Policy",
                section="4.2 Approval thresholds",
                version="3.1",
                status="current",
                score=0.91,
            )
        ]
        session.add_all([user_message, assistant_message])
        session.flush()
    return conversation.id


def test_history_is_newest_first_paginated_and_excludes_empty_conversations(
    history_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, test_sessions = history_client
    now = datetime.now(UTC)
    with test_sessions() as session:
        older_id = seed_conversation(
            session, title="Older question", last_at=now - timedelta(days=1)
        )
        newer_id = seed_conversation(session, title="Newer question", last_at=now)
        seed_conversation(session, title="Empty", last_at=now + timedelta(days=1), with_turn=False)
        session.commit()

    first_page = client.get("/conversations?limit=1&offset=0")
    second_page = client.get("/conversations?limit=1&offset=1")

    assert first_page.status_code == 200
    assert first_page.json()["total"] == 2
    assert first_page.json()["conversations"][0]["id"] == str(newer_id)
    assert first_page.json()["conversations"][0]["preview"] == "Newer question"
    assert second_page.json()["conversations"][0]["id"] == str(older_id)


def test_history_detail_returns_turns_and_citations(
    history_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, test_sessions = history_client
    with test_sessions() as session:
        conversation_id = seed_conversation(
            session, title="Approval threshold?", last_at=datetime.now(UTC)
        )
        session.commit()

    response = client.get(f"/conversations/{conversation_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(conversation_id)
    assert [message["role"] for message in body["messages"]] == ["user", "assistant"]
    assert body["messages"][1]["citations"][0]["section"] == "4.2 Approval thresholds"
    assert body["messages"][1]["citations"][0]["version"] == "3.1"


def test_history_detail_returns_404_for_unknown_conversation(
    history_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = history_client

    response = client.get(f"/conversations/{UUID(int=1)}")

    assert response.status_code == 404
