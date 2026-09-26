"""GET /conversations -- the list behind /history. F8.

Rows are seeded through the ORM rather than by asking questions. This suite is
about the *list* -- its order, its derived title, and what it leaves out -- and
driving it through /ask would drag retrieval and generation into a test that
has nothing to do with either, so it would go red for reasons that are not
about the list.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import database
from app.core.database import Base, session_scope
from app.core.models import Conversation, Message, now

EPOCH = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch) -> None:
    """Postgres, replaced by SQLite in memory -- the models are portable."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},  # TestClient runs def endpoints in a thread
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        database,
        "SessionLocal",
        sessionmaker(bind=engine, autoflush=False, expire_on_commit=False),
    )


def seed(
    conversation_id: str,
    turns: list[tuple[str, str]],
    *,
    minutes: int = 0,
) -> None:
    """A conversation with its turns, last touched `minutes` after the epoch.

    Turns are stored in the order given; `now()` is strictly increasing, so
    the first user turn really is the first one back out.
    """
    touched = EPOCH + timedelta(minutes=minutes)
    with session_scope() as db:
        db.add(Conversation(id=conversation_id, started_at=touched, last_at=touched))
        db.flush()
        for role, content in turns:
            db.add(
                Message(
                    conversation_id=conversation_id,
                    role=role,
                    content=content,
                    created_at=now(),
                )
            )


def listed(client: TestClient, query: str = "") -> list[dict]:
    response = client.get(f"/conversations{query}")
    assert response.status_code == 200, response.text
    return response.json()


ANSWER = "Claims of 75 pounds or more require line-manager approval."


# --- the contract ----------------------------------------------------------


def test_a_row_carries_what_it_takes_to_recognise_a_conversation(
    client: TestClient, db: None
) -> None:
    """REQ-C8 / REQ-A6: PRD section 5, field for field."""
    seed("c1", [("user", "What is the approval threshold?"), ("assistant", ANSWER)])

    row = listed(client)[0]

    assert set(row) == {"id", "started_at", "last_at", "title", "message_count"}
    assert row["id"] == "c1"
    assert row["title"] == "What is the approval threshold?"
    assert row["message_count"] == 2
    assert row["started_at"] and row["last_at"]


# --- order -----------------------------------------------------------------


def test_conversations_come_back_newest_first(client: TestClient, db: None) -> None:
    """REQ-C8. Ordered on last_at: the thread you were just in is on top."""
    seed("oldest", [("user", "Oldest")], minutes=0)
    seed("newest", [("user", "Newest")], minutes=30)
    seed("middle", [("user", "Middle")], minutes=15)

    assert [row["id"] for row in listed(client)] == ["newest", "middle", "oldest"]


def test_a_continued_conversation_moves_to_the_top(client: TestClient, db: None) -> None:
    """Started first, touched last -- the list is about the second one."""
    seed("old-thread", [("user", "Asked in March")], minutes=0)
    seed("new-thread", [("user", "Asked in April")], minutes=10)

    with session_scope() as session:
        session.get(Conversation, "old-thread").last_at = EPOCH + timedelta(minutes=99)

    assert [row["id"] for row in listed(client)] == ["old-thread", "new-thread"]


# --- the derived title -----------------------------------------------------


def test_the_title_is_the_first_user_question(client: TestClient, db: None) -> None:
    """Not the latest question, and never the assistant's answer."""
    seed(
        "c1",
        [
            ("user", "How often do we refresh KYC for a high-risk client?"),
            ("assistant", "Every twelve months."),
            ("user", "And for a medium-risk one?"),
            ("assistant", "Every three years."),
        ],
    )

    assert listed(client)[0]["title"] == "How often do we refresh KYC for a high-risk client?"


def test_a_long_question_is_truncated_with_an_ellipsis(client: TestClient, db: None) -> None:
    question = (
        "What is the approval threshold for a travel expense claim submitted by a "
        "contractor working out of the Frankfurt office?"
    )
    seed("c1", [("user", question)])

    title = listed(client)[0]["title"]

    assert len(title) == 80
    assert title.endswith("…")
    assert question.startswith(title[:-1])


def test_a_question_that_fits_keeps_every_character(client: TestClient, db: None) -> None:
    """80 is the limit, not the point at which trimming starts."""
    question = "x" * 80
    seed("c1", [("user", question)])

    assert listed(client)[0]["title"] == question


def test_a_title_is_one_line(client: TestClient, db: None) -> None:
    """A question pasted out of an email arrives with newlines in it."""
    seed("c1", [("user", "  What is the\n  approval threshold?  ")])

    assert listed(client)[0]["title"] == "What is the approval threshold?"


# --- what is left out ------------------------------------------------------


def test_a_conversation_with_no_turns_is_never_listed(client: TestClient, db: None) -> None:
    """REQ-U14. /ask opens the conversation before it stores anything, so a
    failed write leaves an empty one behind. It cannot be opened, so it is not
    offered."""
    seed("empty", [], minutes=60)  # newest, and still must not appear
    seed("real", [("user", "What is the approval threshold?")], minutes=0)

    assert [row["id"] for row in listed(client)] == ["real"]


def test_nothing_stored_is_an_empty_list_not_an_error(client: TestClient, db: None) -> None:
    assert listed(client) == []


# --- paging ----------------------------------------------------------------


def test_limit_caps_the_rows_returned(client: TestClient, db: None) -> None:
    """REQ-A6. The newest ones, not an arbitrary two."""
    for index in range(5):
        seed(f"c{index}", [("user", f"Question {index}")], minutes=index)

    assert [row["id"] for row in listed(client, "?limit=2")] == ["c4", "c3"]


def test_the_default_limit_is_fifty(client: TestClient, db: None) -> None:
    for index in range(51):
        seed(f"c{index}", [("user", f"Question {index}")], minutes=index)

    assert len(listed(client)) == 50


def test_a_limit_beyond_the_ceiling_is_refused(client: TestClient, db: None) -> None:
    """A page size is a contract, not a suggestion -- 201 is a client bug."""
    assert client.get("/conversations?limit=201").status_code == 422


# --- the count -------------------------------------------------------------


def test_message_count_counts_questions_and_answers(client: TestClient, db: None) -> None:
    """REQ-C2 stores both halves of a turn; the row says how many there are."""
    seed(
        "c1",
        [
            ("user", "What is the approval threshold?"),
            ("assistant", ANSWER),
            ("user", "And above 500?"),
            ("assistant", "Two signatures."),
        ],
    )
    seed("c2", [("user", "How long do we keep client correspondence?")], minutes=5)

    counts = {row["id"]: row["message_count"] for row in listed(client)}

    assert counts == {"c1": 4, "c2": 1}
