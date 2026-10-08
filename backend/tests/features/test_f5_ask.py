"""F5 -- POST /ask. Criteria C7, C8, C10, C11 and C22 at the API, plus the
deterministic half of C30 (both conflicting sections are cited).

The store and model are fakes and the database is SQLite in memory, so this runs
in CI. MIN_SCORE below is a fixture value on the fake model's bag-of-words
scale -- it is NOT table 3's D2 threshold, which is still awaiting sign-off.
"""

from __future__ import annotations

import dataclasses
import logging
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.ask import AskDeps, get_deps
from app.core.database import Base, get_session
from app.core.models import Message, MessageCitation
from app.ingest import corpus
from app.ingest.ingest import ingest
from app.main import app
from app.retrieve.store import Hit

CORPUS = Path(__file__).resolve().parents[2] / "corpus"
FAKE_SCALE_MIN_SCORE = 0.3

ANSWERABLE = "What approval thresholds apply to a travel expense claim?"
UNANSWERABLE = "How many days of paid parental leave am I entitled to?"


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def indexed(store, model):
    ingest(store, model.embed, corpus_dir=CORPUS, max_tokens=400, overlap_tokens=0,
           batch_size=96)
    return store


def api(db, store, *, embed, generate, enabled=True):
    def session():
        s = db()
        try:
            yield s
            s.commit()
        finally:
            s.close()

    app.dependency_overrides[get_session] = session
    app.dependency_overrides[get_deps] = lambda: AskDeps(
        store=store, embed=embed, generate=generate, documents=corpus.load(CORPUS),
        top_k=5, min_score=FAKE_SCALE_MIN_SCORE, context_messages=5,
        generation_enabled=enabled, model_name="fake-model",
    )
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


def test_an_answerable_question_is_answered_with_citations(db, indexed, model):
    body = api(db, indexed, embed=model.embed, generate=model.generate).post(
        "/ask", json={"question": ANSWERABLE}).json()

    assert body["outcome"] == "answered"
    assert body["answer"] == model.answer
    assert body["citations"]
    for c in body["citations"]:  # C10: document, section, version, status
        assert c["document_title"] and c["section"] and c["version"]
        assert c["status"] in {"current", "superseded"}
    uuid.UUID(body["conversation_id"]), uuid.UUID(body["message_id"])
    assert isinstance(body["latency_ms"], int)


def test_c11_a_superseded_citation_says_so(db, indexed, model):
    body = api(db, indexed, embed=model.embed, generate=model.generate).post(
        "/ask", json={"question": ANSWERABLE}).json()

    versions = {(c["version"], c["status"]) for c in body["citations"]}
    assert ("3.0", "superseded") in versions
    assert ("3.1", "current") in versions


def test_c7_a_refusal_never_calls_the_model(db, indexed, model):
    body = api(db, indexed, embed=model.embed, generate=model.generate).post(
        "/ask", json={"question": UNANSWERABLE}).json()

    assert body["outcome"] == "refused"
    assert body["citations"] == []
    assert "do not support an answer" in body["answer"]
    assert not model.was_called


def test_c8_the_kill_switch_returns_passages_and_no_answer(db, indexed, model):
    body = api(db, indexed, embed=model.embed, generate=model.generate, enabled=False).post(
        "/ask", json={"question": ANSWERABLE}).json()

    assert body["outcome"] == "degraded"
    assert body["answer"] is None
    assert body["citations"] and all(c["text"] for c in body["citations"])
    assert not model.was_called


def test_c8_an_unreachable_model_degrades(db, indexed, model, failing_model):
    body = api(db, indexed, embed=model.embed, generate=failing_model.generate).post(
        "/ask", json={"question": ANSWERABLE}).json()

    assert body["outcome"] == "degraded"
    assert body["answer"] is None and body["citations"]


def test_search_unavailable_is_an_error_not_a_refusal(db, indexed, failing_model):
    response = api(db, indexed, embed=failing_model.embed,
                   generate=failing_model.generate).post("/ask", json={"question": ANSWERABLE})

    assert response.status_code == 503


class StubStore:
    """Returns exactly the passages a test names."""

    def __init__(self, hits):
        self.hits = hits

    def search(self, embedding, limit=5, min_score=0.0):
        return [h for h in self.hits if h.score >= min_score][:limit]


def test_c30_both_conflicting_sections_are_cited(db, model):
    conflict = [
        Hit("a", "Destroy within five years of termination.", "outsourcing-third-party",
            "Outsourcing and Third-Party Risk Policy", "6.4 Return and destruction on exit",
            0.6, {"version": "1.8", "status": "current"}),
        Hit("b", "Seven years from the end of the relationship.", "records-retention",
            "Records Retention and Data Handling Policy", "4.1 General table",
            0.55, {"version": "4.0", "status": "current"}),
    ]
    body = api(db, StubStore(conflict), embed=model.embed, generate=model.generate).post(
        "/ask", json={"question": "How long can a provider keep correspondence?"}).json()

    cited = {(c["document_id"], c["section"]) for c in body["citations"]}
    assert ("outsourcing-third-party", "6.4 Return and destruction on exit") in cited
    assert ("records-retention", "4.1 General table") in cited


def test_every_turn_and_its_citations_are_stored(db, indexed, model):
    client = api(db, indexed, embed=model.embed, generate=model.generate)
    first = client.post("/ask", json={"question": UNANSWERABLE}).json()
    second = client.post("/ask", json={"question": ANSWERABLE,
                                       "conversation_id": first["conversation_id"]}).json()

    with db() as s:
        rows = s.execute(select(Message.role, Message.content, Message.outcome)
                         .order_by(Message.created_at)).all()
        cited = s.scalar(select(func.count()).select_from(MessageCitation))
    assert [r.role for r in rows] == ["user", "assistant", "user", "assistant"]
    assert rows[0].content == UNANSWERABLE and rows[2].content == ANSWERABLE
    assert [r.outcome for r in rows[1::2]] == ["refused", "answered"]
    assert cited == len(second["citations"])


def test_an_unknown_conversation_is_not_found(db, indexed, model):
    response = api(db, indexed, embed=model.embed, generate=model.generate).post(
        "/ask", json={"question": ANSWERABLE, "conversation_id": str(uuid.uuid4())})

    assert response.status_code == 404


def test_c22_the_question_is_never_logged(db, indexed, model, caplog):
    secret = "Zanzibar approval thresholds for a travel expense claim"
    with caplog.at_level(logging.DEBUG):
        api(db, indexed, embed=model.embed, generate=model.generate).post(
            "/ask", json={"question": secret})

    assert caplog.records, "something should be logged, or this test proves nothing"
    assert not any("Zanzibar" in r.getMessage() for r in caplog.records)


def test_an_unset_threshold_is_a_clear_503_not_a_guess(monkeypatch):
    from app.api import ask as module

    unset = dataclasses.replace(module.settings, min_score=None, retrieve_top_k=5)
    monkeypatch.setattr(module, "settings", unset)
    response = TestClient(app).post("/ask", json={"question": ANSWERABLE})

    assert response.status_code == 503
    assert "MIN_SCORE" in response.json()["detail"]
