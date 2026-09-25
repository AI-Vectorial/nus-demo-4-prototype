"""Proof the fixtures work, and a worked example of using them.

Delete this file if you like -- but read it first. It is the shortest
demonstration of how to test the two behaviours that are hardest to test and
matter most: that a refusal does not call the model, and that degraded mode
returns something useful.
"""

from __future__ import annotations

from tests.fixtures.fake_model import FakeModel
from tests.fixtures.fake_store import FakeVectorStore


def test_the_store_returns_the_right_passage(loaded_store, model):
    """Ask about approval, get the approval passage -- not one of the others."""
    query = model.embed(["What is the approval threshold for expenses?"])[0]
    hits = loaded_store.search(query, limit=1)

    assert hits
    assert hits[0].document_id == "travel-expense-policy"
    assert "75" in hits[0].text


def test_a_threshold_can_filter_everything_out(loaded_store, model):
    """The mechanism a refusal is built on."""
    query = model.embed(["something entirely unrelated to banking policy"])[0]
    hits = loaded_store.search(query, limit=5, min_score=0.99)

    assert hits == []


def test_a_refusal_must_not_call_the_model(loaded_store, model):
    """The assertion that makes REQ-R3 checkable.

    If retrieval finds nothing above the threshold, generation must not run.
    A model asked a question it has no context for will answer anyway --
    observed with gpt-oss-120b, which restated irrelevant policy rather than
    declining. So the rule has to live in code, not in a prompt.
    """
    query = model.embed(["how much parental leave am I entitled to"])[0]
    hits = loaded_store.search(query, limit=5, min_score=0.99)

    if not hits:
        pass  # your code refuses here, and must not reach the model
    else:
        model.generate("...")

    assert not model.was_called, (
        "The model was called despite retrieval finding nothing. "
        "This is the failure the product exists to prevent."
    )


def test_degraded_mode_is_testable(loaded_store, failing_model):
    """REQ-G6, without unplugging anything."""
    from app.generate import ProviderError

    query = FakeModel().embed(["approval threshold"])[0]
    hits = loaded_store.search(query, limit=3)
    assert hits, "we have passages -- the model is what is unavailable"

    try:
        failing_model.generate("compose an answer")
        raise AssertionError("the failing model should have raised")
    except ProviderError:
        # Your code returns the passages with no answer and a degraded flag.
        pass


def test_the_fake_store_satisfies_the_real_interface():
    from app.retrieve.store import VectorStore

    assert isinstance(FakeVectorStore(), VectorStore)
