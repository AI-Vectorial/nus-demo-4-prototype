"""POST /ask and the conversation behind it -- F5/F6.

Retrieval and generation are substituted here. That is not a shortcut: this
suite is about the *turn* -- the contract, the fork between answering and
refusing, what gets written down and what a follow-up sees. Whether the right
passage comes back is retrieval's own test, and mixing the two gives a suite
that goes red for reasons that have nothing to do with the endpoint.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field, replace
from types import ModuleType

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import database
from app.core.config import settings
from app.core.database import Base
from app.retrieve.store import Hit

# --- stand-ins for the modules built alongside this one --------------------
#
# Substituted through sys.modules rather than by patching a name in app.api.ask,
# because the endpoint imports them at call time -- so these are what it gets.


@dataclass(frozen=True)
class Grounded:
    passages: list[Hit]


@dataclass(frozen=True)
class Insufficient:
    reason: str
    best_score: float = 0.0
    owner_hint: str | None = None


@dataclass
class Answer:
    text: str | None = "Claims of 75 pounds or more require line-manager approval."
    citations: list = field(default_factory=list)
    degraded: bool = False
    prompt_version: str = "answer.v1"
    model: str = "openai/gpt-oss-120b"
    latency_ms: int = 1840


def hit(section: str, score: float, *, status: str = "current", version: str = "3.1") -> Hit:
    return Hit(
        passage_id=f"{section}-{score}",
        text=f"The text of {section}.",
        document_id="travel-expense-policy",
        document_title="Travel and Expense Policy",
        section=section,
        score=score,
        metadata={"version": version, "status": status},
    )


class FakePipeline:
    """Retrieval and generation, recorded rather than performed."""

    def __init__(self) -> None:
        self.result: object = Grounded([hit("4.2 Approval thresholds", 0.82)])
        self.answer = Answer()
        self.questions: list[str] = []
        self.histories: list[list[tuple[str, str]] | None] = []

    def retrieve(self, question: str) -> object:
        self.questions.append(question)
        return self.result

    def compose(self, result: object, history: list[tuple[str, str]] | None = None) -> Answer:
        self.histories.append(history)
        return self.answer

    @property
    def model_was_called(self) -> bool:
        """The assertion a refusal test needs."""
        return bool(self.histories)


@pytest.fixture
def pipeline(monkeypatch: pytest.MonkeyPatch) -> FakePipeline:
    fake = FakePipeline()

    retrieve_service = ModuleType("app.retrieve.service")
    retrieve_service.retrieve = fake.retrieve  # type: ignore[attr-defined]
    retrieve_service.Grounded = Grounded  # type: ignore[attr-defined]
    retrieve_service.Insufficient = Insufficient  # type: ignore[attr-defined]

    generate_service = ModuleType("app.generate.service")
    generate_service.answer = fake.compose  # type: ignore[attr-defined]
    generate_service.Answer = Answer  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "app.retrieve.service", retrieve_service)
    monkeypatch.setitem(sys.modules, "app.generate.service", generate_service)
    return fake


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch) -> None:
    """Postgres, replaced by SQLite in memory.

    The models are deliberately portable -- uuid strings, no server defaults --
    so persistence can be asserted without a database server in the loop.
    """
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


def ask(client: TestClient, question: str, conversation_id: str | None = None) -> dict:
    response = client.post(
        "/ask", json={"question": question, "conversation_id": conversation_id}
    )
    assert response.status_code == 200, response.text
    return response.json()


# --- the three outcomes ----------------------------------------------------


def test_an_answer_returns_the_contract_shape(
    client: TestClient, pipeline: FakePipeline, db: None
) -> None:
    """REQ-A1/A2: PRD section 5, field for field."""
    body = ask(client, "What is the approval threshold?")

    assert body["outcome"] == "answered"
    assert body["answer"] == pipeline.answer.text
    assert body["citations"] == [
        {
            "document_id": "travel-expense-policy",
            "document_title": "Travel and Expense Policy",
            "section": "4.2 Approval thresholds",
            "version": "3.1",
            "status": "current",
            "score": 0.82,
        }
    ]
    assert body["conversation_id"]
    assert body["message_id"]
    assert isinstance(body["latency_ms"], int)
    assert set(body) == {
        "outcome",
        "answer",
        "citations",
        "conversation_id",
        "message_id",
        "latency_ms",
    }


def test_a_refusal_makes_no_model_call(
    client: TestClient, pipeline: FakePipeline, db: None
) -> None:
    """REQ-R3 and NFR-2. The model is never asked whether it knows something."""
    pipeline.result = Insufficient(
        reason="Nothing in the corpus covers expenses for a partner or dependant.",
        best_score=0.11,
        owner_hint="Group Finance",
    )

    body = ask(client, "Can I expense my partner's flight?")

    assert body["outcome"] == "refused"
    assert body["citations"] == []
    assert not pipeline.model_was_called


def test_a_refusal_says_where_to_go_instead(
    client: TestClient, pipeline: FakePipeline, db: None
) -> None:
    """D5: "I don't know" leaves the user where they started."""
    pipeline.result = Insufficient(
        reason="The Travel and Expense Policy is silent on accompanying family.",
        best_score=0.11,
        owner_hint="Group Finance",
    )

    body = ask(client, "Can I expense my partner's flight?")

    assert "Group Finance" in body["answer"]
    assert "silent on accompanying family" in body["answer"]


def test_degraded_returns_the_passages_and_no_answer(
    client: TestClient, pipeline: FakePipeline, db: None
) -> None:
    """REQ-G6: the model is off, and what is left is still a policy search."""
    pipeline.answer = Answer(text=None, degraded=True, model="", prompt_version="")

    body = ask(client, "What is the approval threshold?")

    assert body["outcome"] == "degraded"
    assert body["answer"] is None
    assert body["citations"], "degraded must still return what retrieval found"


def test_citations_are_one_per_section(
    client: TestClient, pipeline: FakePipeline, db: None
) -> None:
    """D7: two passages from 4.2 are one citation, and the best score wins."""
    pipeline.result = Grounded(
        [
            hit("4.2 Approval thresholds", 0.82),
            hit("4.2 Approval thresholds", 0.61),
            hit("4.5 Self-approval", 0.55),
        ]
    )

    citations = ask(client, "What is the approval threshold?")["citations"]

    assert [citation["section"] for citation in citations] == [
        "4.2 Approval thresholds",
        "4.5 Self-approval",
    ]
    assert citations[0]["score"] == 0.82


def test_a_superseded_passage_keeps_its_status(
    client: TestClient, pipeline: FakePipeline, db: None
) -> None:
    """REQ-U4 needs the status on the wire to distinguish it in the interface."""
    pipeline.result = Grounded(
        [hit("4.2 Approval thresholds", 0.79, status="superseded", version="3.0")]
    )

    citation = ask(client, "What was the old threshold?")["citations"][0]

    assert citation["status"] == "superseded"
    assert citation["version"] == "3.0"


# --- the conversation ------------------------------------------------------


def test_the_turn_is_stored_against_its_conversation(
    client: TestClient, pipeline: FakePipeline, db: None
) -> None:
    """REQ-C1, REQ-C2, REQ-A3."""
    body = ask(client, "What is the approval threshold?")

    stored = client.get(f"/conversations/{body['conversation_id']}")
    assert stored.status_code == 200
    conversation = stored.json()

    assert [message["role"] for message in conversation["messages"]] == ["user", "assistant"]
    question, answer = conversation["messages"]
    assert question["content"] == "What is the approval threshold?"
    assert answer["id"] == body["message_id"]
    assert answer["outcome"] == "answered"
    assert answer["model"] == "openai/gpt-oss-120b"
    assert answer["prompt_version"] == "answer.v1"
    assert answer["latency_ms"] == 1840
    assert answer["citations"][0]["section"] == "4.2 Approval thresholds"


def test_a_follow_up_continues_the_same_conversation(
    client: TestClient, pipeline: FakePipeline, db: None
) -> None:
    """REQ-U8: the thread above the follow-up is not lost."""
    first = ask(client, "What is the approval threshold?")
    second = ask(client, "And what about above 500?", first["conversation_id"])

    assert second["conversation_id"] == first["conversation_id"]
    assert second["message_id"] != first["message_id"]

    conversation = client.get(f"/conversations/{first['conversation_id']}").json()
    assert len(conversation["messages"]) == 4
    assert [message["role"] for message in conversation["messages"]] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]


def test_a_follow_up_is_answered_with_the_recent_turns(
    client: TestClient, pipeline: FakePipeline, db: None
) -> None:
    """REQ-C3: oldest first, so "above 500?" has something to refer to."""
    first = ask(client, "What is the approval threshold?")
    ask(client, "And what about above 500?", first["conversation_id"])

    history = pipeline.histories[-1]
    assert history == [
        ("user", "What is the approval threshold?"),
        ("assistant", pipeline.answer.text),
        ("user", "And what about above 500?"),
    ]


def test_retrieval_runs_on_every_turn(
    client: TestClient, pipeline: FakePipeline, db: None
) -> None:
    """REQ-C5 / D9. The trap: reusing the first turn's passages still looks right."""
    first = ask(client, "What is the approval threshold?")
    ask(client, "And what about above 500?", first["conversation_id"])

    assert pipeline.questions == [
        "What is the approval threshold?",
        "And what about above 500?",
    ]


def test_the_context_window_is_capped(
    client: TestClient, pipeline: FakePipeline, db: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """REQ-C4 / D8: CONTEXT_MESSAGES turns, not the whole conversation."""
    # Settings are frozen, so the endpoint's whole view of them is replaced.
    monkeypatch.setattr("app.api.ask.settings", replace(settings, context_messages=3))

    conversation_id = None
    for index in range(4):
        conversation_id = ask(client, f"Question {index}", conversation_id)["conversation_id"]

    history = pipeline.histories[-1]
    assert len(history) == 3
    assert history[-1] == ("user", "Question 3")


def test_new_chat_starts_clean(client: TestClient, pipeline: FakePipeline, db: None) -> None:
    """REQ-C6: no conversation_id means no prior context."""
    first = ask(client, "What is the approval threshold?")
    second = ask(client, "And what about above 500?")

    assert second["conversation_id"] != first["conversation_id"]
    assert pipeline.histories[-1] == [("user", "And what about above 500?")]


def test_an_unknown_conversation_is_404(client: TestClient, db: None) -> None:
    assert client.get("/conversations/9c1e-does-not-exist").status_code == 404


# --- what must not break the product ---------------------------------------


def test_the_answer_survives_a_failed_write(
    client: TestClient, pipeline: FakePipeline, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A storage problem must not become a product failure.

    No `db` fixture here: the database is unreachable for the whole turn, and
    the user still gets their cited answer.
    """
    monkeypatch.setattr(database, "SessionLocal", None)

    body = ask(client, "What is the approval threshold?")

    assert body["outcome"] == "answered"
    assert body["answer"] == pipeline.answer.text
    assert body["citations"]
    assert body["conversation_id"] and body["message_id"]


def test_an_empty_question_is_rejected(client: TestClient, pipeline: FakePipeline) -> None:
    """Nothing reaches retrieval, and the client is told why."""
    response = client.post("/ask", json={"question": "", "conversation_id": None})

    assert response.status_code == 422
    assert pipeline.questions == []
