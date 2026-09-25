"""Fixtures, so writing a test costs seconds rather than twenty minutes.

Your acceptance criteria are the specification, and CI runs them. If the first
test is expensive to write, it does not get written -- and the module's claim
that acceptance criteria are executable becomes a slogan.

    def test_a_question_the_corpus_cannot_answer_refuses(store, model):
        ...
        assert not model.was_called
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.retrieve.store import Passage
from tests.fixtures.fake_model import FakeModel
from tests.fixtures.fake_store import FakeVectorStore

FIXTURE_CORPUS = Path(__file__).parent / "fixtures" / "corpus"


@pytest.fixture
def client() -> TestClient:
    """The API, loaded. Use it to assert on real responses."""
    return TestClient(app)


@pytest.fixture
def store() -> FakeVectorStore:
    """An empty in-memory vector store. No Qdrant required."""
    return FakeVectorStore()


@pytest.fixture
def model() -> FakeModel:
    """A model that never touches the network."""
    return FakeModel()


@pytest.fixture
def failing_model() -> FakeModel:
    """A model that is always unreachable -- for testing degraded mode."""
    return FakeModel(fail=True)


@pytest.fixture
def sample_corpus() -> Path:
    """Three tiny policy documents. Small enough to embed inside a test."""
    return FIXTURE_CORPUS


@pytest.fixture
def passages(model: FakeModel) -> list[Passage]:
    """Three embedded passages, ready to upsert.

    Deliberately about different things, so a test that asserts the RIGHT one
    came back is actually asserting something.
    """
    texts = [
        ("travel-expense-policy", "Travel and Expense Policy", "4.2 Approval thresholds",
         "Claims of 75 pounds or more require line-manager approval before reimbursement."),
        ("records-retention", "Records Retention and Data Handling Policy", "4.1 General table",
         "Client correspondence is retained for seven years from the end of the relationship."),
        ("client-onboarding-kyc", "Client Onboarding and KYC Refresh Policy", "6.1 Refresh cycles",
         "A client rated High is refreshed every twelve months."),
    ]
    vectors = model.embed([text for *_, text in texts])
    return [
        Passage(
            id=f"p{index}",
            text=text,
            document_id=doc_id,
            document_title=title,
            section=section,
            embedding=vector,
            metadata={"version": "1.0", "status": "current"},
        )
        for index, ((doc_id, title, section, text), vector) in enumerate(
            zip(texts, vectors, strict=True)
        )
    ]


@pytest.fixture
def loaded_store(store: FakeVectorStore, passages: list[Passage]) -> FakeVectorStore:
    """A vector store with the three passages already in it."""
    store.ensure_ready()
    store.upsert(passages)
    return store
