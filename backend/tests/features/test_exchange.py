"""F3 refuse, F4 generate, F5 ask, F6 follow-up, F7 corpus, F8 history.

No Qdrant, no network, no Postgres: a stub store, a fake model, and SQLite.
The live retrieval check against the real index is tests/eval/run.py.
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.features.ask as ask_module
from app.core.config import settings
from app.core.database import Base, get_session
from app.core.records import Conversation, Message
from app.features.ask import citations_for
from app.generate import ProviderError
from app.generate.compose import PROMPT_VERSION, build_user_message, system_prompt
from app.main import app
from app.retrieve.ground import REFUSAL_REASON, Grounded, Insufficient, ground
from app.retrieve.store import Hit

REAL_CORPUS = Path(__file__).resolve().parents[2] / "corpus"


# --------------------------------------------------------------------- helpers


def _hit(score: float, status: str = "current", section: str = "4.2 Approval thresholds",
         version: str = "3.1", doc: str = "travel-expense-policy") -> Hit:
    return Hit(
        passage_id=f"{doc}-{version}-{section}-{score}",
        text="Claims of 75 pounds or more require line-manager approval.",
        document_id=doc,
        document_title="Travel and Expense Policy",
        section=section,
        score=score,
        metadata={"status": status, "version": version},
    )


class StubStore:
    """Returns fixed hits, filtered by min_score the way Qdrant does."""

    def __init__(self, hits: list[Hit]) -> None:
        self.hits = hits
        self.queries: list[list[float]] = []

    def search(self, embedding, limit=5, min_score=0.0):
        self.queries.append(embedding)
        return [h for h in self.hits if h.score >= min_score][:limit]

    def ensure_ready(self):
        pass

    def count(self):
        return len(self.hits)


def _embed_recorder(sink: list[str]):
    def embed(texts: list[str]) -> list[list[float]]:
        sink.extend(texts)
        return [[1.0, 0.0]] * len(texts)

    return embed


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    import app.core.records  # noqa: F401 - registers the models

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def wire(monkeypatch, db):
    """Route the ask flow to a stub store, a recording embed and a spy composer."""
    state = {
        "hits": [_hit(0.9)],
        "queries": [],
        "composed": [],
        "compose_error": None,
        "compose_text": "Claims of 75 need approval.",
    }

    def configure(hits=None, compose_error=None, compose_text="Claims of 75 need approval."):
        state["hits"] = hits if hits is not None else state["hits"]
        state["compose_error"] = compose_error
        state["compose_text"] = compose_text

    def fake_store():
        return StubStore(state["hits"])

    def fake_embed(texts):
        state["queries"].extend(texts)
        return [[1.0, 0.0]] * len(texts)

    def fake_compose(question, passages, earlier):
        state["composed"].append({"question": question, "earlier": list(earlier)})
        if state["compose_error"] is not None:
            raise state["compose_error"]
        return state["compose_text"]

    monkeypatch.setattr(ask_module, "get_vector_store", fake_store)
    monkeypatch.setattr(ask_module, "embed", fake_embed)
    monkeypatch.setattr(ask_module, "compose_answer", fake_compose)

    def override():
        yield db
        db.commit()

    app.dependency_overrides[get_session] = override
    yield state, configure
    app.dependency_overrides.clear()


@pytest.fixture
def client(wire) -> TestClient:
    return TestClient(app)


# ----------------------------------------------------- F3 -- refuse (REQ-R2, R3, R6)


def test_nothing_above_the_threshold_is_insufficient():
    result = ground(StubStore([_hit(0.3)]), lambda t: [[1.0, 0.0]] * len(t), "crypto",
                    min_score=0.518)

    assert isinstance(result, Insufficient)


def test_a_passage_above_the_threshold_is_grounded():
    result = ground(StubStore([_hit(0.9)]), lambda t: [[1.0, 0.0]] * len(t), "q", min_score=0.518)

    assert isinstance(result, Grounded)
    assert result.passages[0].score == 0.9


def test_passages_below_the_threshold_are_discarded():
    result = ground(
        StubStore([_hit(0.52), _hit(0.50)]), lambda t: [[1.0, 0.0]] * len(t), "q", min_score=0.518
    )

    assert [h.score for h in result.passages] == [0.52]


def test_the_refusal_names_group_finance():
    assert "Group Finance" in REFUSAL_REASON


def test_the_threshold_comes_from_configuration_not_code():
    assert settings.min_score == pytest.approx(0.518)


def test_a_refusal_never_calls_the_model(client, wire):
    state, configure = wire
    configure(hits=[_hit(0.3)])

    response = client.post("/ask", json={"question": "Can I expense my partner's flight?"})

    body = response.json()
    assert body["outcome"] == "refused"
    assert body["citations"] == []
    assert "Group Finance" in body["answer"]
    assert state["composed"] == []


# ------------------------------------------------------- F4 -- generate (REQ-G1 to G6)


def test_the_prompt_is_a_versioned_file_and_is_recorded():
    assert PROMPT_VERSION == "answer-v1"
    assert "Use only the policy passages" in system_prompt()


def test_the_prompt_forbids_choosing_between_conflicting_policies():
    text = " ".join(system_prompt().split())

    assert "Do not choose which rule applies" in text


def test_the_user_message_carries_only_the_passages_and_the_question():
    message = build_user_message("How much?", [_hit(0.9)], earlier=[])

    assert "Travel and Expense Policy — 4.2 Approval thresholds" in message
    assert message.endswith("Question: How much?")


def test_superseded_passages_are_marked_for_the_model():
    message = build_user_message("q", [_hit(0.9, status="superseded", version="3.0")], [])

    assert "SUPERSEDED" in message


def test_an_answer_records_its_model_and_prompt_version(client, db):
    response = client.post("/ask", json={"question": "What is the threshold?"})

    assert response.json()["outcome"] == "answered"
    assistant = db.query(Message).filter(Message.role == "assistant").one()
    assert assistant.prompt_version == PROMPT_VERSION
    assert assistant.model == settings.llm_model
    assert assistant.latency_ms is not None


def test_generation_disabled_returns_degraded_with_passages_and_no_answer(
    client, wire, monkeypatch
):
    state, _ = wire
    monkeypatch.setattr(ask_module, "settings", replace(settings, generation_enabled=False))

    body = client.post("/ask", json={"question": "threshold?"}).json()

    assert body["outcome"] == "degraded"
    assert body["answer"] is None
    assert len(body["citations"]) == 1
    assert state["composed"] == []


def test_an_unreachable_provider_returns_degraded(client, wire):
    _, configure = wire
    configure(compose_error=ProviderError("generate failed (fake)", retryable=True))

    body = client.post("/ask", json={"question": "threshold?"}).json()

    assert body["outcome"] == "degraded"
    assert body["answer"] is None
    assert body["citations"]


# ------------------------------------------------------- F5 -- ask (REQ-A1, A2, C1, C2)


def test_the_response_matches_the_contract(client):
    body = client.post("/ask", json={"question": "threshold?"}).json()

    assert set(body) == {"outcome", "answer", "citations", "conversation_id", "message_id",
                         "latency_ms"}
    assert set(body["citations"][0]) == {"document_id", "document_title", "section",
                                         "version", "status", "score"}


def test_the_first_question_starts_a_conversation_and_both_turns_are_stored(client, db):
    body = client.post("/ask", json={"question": "threshold?"}).json()

    conversation = db.get(Conversation, uuid.UUID(body["conversation_id"]))
    roles = [m.role for m in conversation.messages]
    assert roles == ["user", "assistant"]


def test_a_blank_question_is_rejected(client):
    assert client.post("/ask", json={"question": "   "}).status_code == 422


def test_an_unknown_conversation_is_not_found(client):
    response = client.post(
        "/ask",
        json={"question": "threshold?", "conversation_id": "00000000-0000-0000-0000-000000000001"},
    )

    assert response.status_code == 404


# ----------------------------------------------- D7 -- one citation per section


def test_citations_are_grouped_by_section_keeping_the_best_score():
    hits = [_hit(0.7), _hit(0.9), _hit(0.8, section="4.3 Other")]

    cites = citations_for(hits)

    assert [c["section"] for c in cites] == ["4.2 Approval thresholds", "4.3 Other"]
    assert cites[0]["score"] == 0.9


def test_a_superseded_citation_carries_its_status_and_version():
    cites = citations_for([_hit(0.8, status="superseded", version="3.0")])

    assert cites[0]["status"] == "superseded"
    assert cites[0]["version"] == "3.0"


# ------------------------------------------------- F6 -- follow-ups (REQ-C3 to C7)


def test_a_follow_up_is_embedded_with_the_earlier_questions_latest_last(client, wire):
    state, _ = wire
    first = client.post("/ask", json={"question": "What is the approval threshold?"}).json()
    state["queries"].clear()

    client.post(
        "/ask",
        json={"question": "And above 500?", "conversation_id": str(first["conversation_id"])},
    )

    assert state["queries"] == ["What is the approval threshold?\nAnd above 500?"]


def test_a_follow_up_is_answered_with_the_earlier_questions_in_context(client, wire):
    state, _ = wire
    first = client.post("/ask", json={"question": "What is the approval threshold?"}).json()

    client.post(
        "/ask",
        json={"question": "And above 500?", "conversation_id": str(first["conversation_id"])},
    )

    assert state["composed"][-1]["earlier"] == ["What is the approval threshold?"]


def test_retrieval_runs_on_every_turn(client, wire):
    state, _ = wire
    first = client.post("/ask", json={"question": "threshold?"}).json()
    store_calls_before = len(state["queries"])

    client.post("/ask", json={"question": "and above 500?",
                              "conversation_id": str(first["conversation_id"])})

    assert len(state["queries"]) > store_calls_before


def test_only_the_configured_number_of_earlier_messages_is_used(client, wire, monkeypatch):
    state, _ = wire
    monkeypatch.setattr(ask_module, "settings", replace(settings, context_messages=2))
    first = client.post("/ask", json={"question": "one"}).json()
    cid = str(first["conversation_id"])
    client.post("/ask", json={"question": "two", "conversation_id": cid})
    client.post("/ask", json={"question": "three", "conversation_id": cid})

    assert state["composed"][-1]["earlier"] == ["two"]


# ----------------------------------------------- F7 -- corpus browser (REQ-B1 to B5, A4)


def test_the_corpus_lists_five_documents_and_flags_the_superseded_one(client):
    documents = client.get("/corpus").json()

    assert len(documents) == 5
    statuses = {d["id"]: d["status"] for d in documents}
    assert statuses["travel-expense-policy-3.0"] == "superseded"
    assert statuses["travel-expense-policy-3.1"] == "current"


def test_a_document_shows_its_sections_and_text(client):
    document = client.get("/corpus/travel-expense-policy-3.1").json()

    headings = [s["heading"] for s in document["sections"]]
    assert "4.2 Approval thresholds" in headings
    assert any("exactly £75" in s["text"] for s in document["sections"])


def test_an_unknown_document_is_not_found(client):
    assert client.get("/corpus/no-such-policy-1.0").status_code == 404


def test_the_corpus_is_read_from_the_directory_not_the_database():
    from app.features.corpus import list_documents

    assert len(list_documents(REAL_CORPUS)) == 5


# ------------------------------------------------------- F8 -- history (REQ-C8, C9, A6)


def test_history_lists_only_conversations_with_turns_newest_first(client, db):
    empty = Conversation()
    db.add(empty)
    db.flush()
    client.post("/ask", json={"question": "older question"})
    client.post("/ask", json={"question": "newer question"})

    listed = client.get("/conversations").json()

    assert len(listed) == 2
    assert all(c["message_count"] >= 2 for c in listed)
    assert listed[0]["title"] == "newer question"


def test_a_long_first_question_is_truncated_for_the_title(client):
    client.post("/ask", json={"question": "x" * 200})

    title = client.get("/conversations").json()[0]["title"]

    assert len(title) == 80
    assert title.endswith("…")


def test_history_is_paginated(client):
    for n in range(3):
        client.post("/ask", json={"question": f"question {n}"})

    page = client.get("/conversations?limit=2&offset=0").json()

    assert len(page) == 2


def test_a_past_conversation_shows_its_turns_and_citations_and_can_be_continued(client):
    first = client.post("/ask", json={"question": "What is the threshold?"}).json()
    cid = first["conversation_id"]

    view = client.get(f"/conversations/{cid}").json()
    assert [m["role"] for m in view["messages"]] == ["user", "assistant"]
    assert view["messages"][1]["citations"]

    follow = client.post("/ask", json={"question": "And above 500?", "conversation_id": cid})
    assert follow.status_code == 200


def test_an_unknown_conversation_detail_is_not_found(client):
    response = client.get("/conversations/00000000-0000-0000-0000-000000000001")

    assert response.status_code == 404


# ------------------------------------------------- Q10 -- the conflict, surfaced not decided


def test_the_conflict_is_named_and_left_open_in_the_prompt():
    text = system_prompt()

    assert "name the conflict" in text
    assert "escalated" in text
