"""F2 -- retrieve. REQ-R1 and the unit side of REQ-R5.

The live check against all ten answerable questions is run separately by
tests/eval/run.py, because it needs the real embedding model and a live index.
"""

from __future__ import annotations

from app.retrieve.search import prefer_current, search
from app.retrieve.store import Hit
from tests.fixtures.fake_model import FakeModel
from tests.fixtures.fake_store import FakeVectorStore


def _hit(passage_id: str, score: float, status: str) -> Hit:
    return Hit(
        passage_id=passage_id,
        text=passage_id,
        document_id="travel-expense-policy",
        document_title="Travel and Expense Policy",
        section="4.2 Approval thresholds",
        score=score,
        metadata={"status": status, "version": "3.1" if status == "current" else "3.0"},
    )


def test_a_current_passage_ranks_ahead_of_a_higher_scoring_superseded_one():
    superseded_best = _hit("old", 0.9, "superseded")
    current_lower = _hit("new", 0.6, "current")

    ordered = prefer_current([superseded_best, current_lower])

    assert [h.passage_id for h in ordered] == ["new", "old"]


def test_order_within_each_status_is_kept():
    hits = [
        _hit("c1", 0.9, "current"),
        _hit("s1", 0.8, "superseded"),
        _hit("c2", 0.7, "current"),
        _hit("s2", 0.6, "superseded"),
    ]

    ordered = prefer_current(hits)

    assert [h.passage_id for h in ordered] == ["c1", "c2", "s1", "s2"]


def test_superseded_passages_are_kept_not_dropped():
    hits = [_hit("c1", 0.9, "current"), _hit("s1", 0.8, "superseded")]

    assert {h.passage_id for h in prefer_current(hits)} == {"c1", "s1"}


def test_search_returns_at_most_top_k(store: FakeVectorStore, model: FakeModel, passages):
    store.ensure_ready()
    store.upsert(passages)

    hits = search(store, model.embed, "approval threshold", top_k=2)

    assert len(hits) == 2


def test_search_finds_the_matching_passage_first(
    store: FakeVectorStore, model: FakeModel, passages
):
    store.ensure_ready()
    store.upsert(passages)

    question = "claims of 75 pounds need line-manager approval"
    hits = search(store, model.embed, question, top_k=3)

    assert hits[0].document_id == "travel-expense-policy"


def test_search_embeds_the_question_it_was_given(store: FakeVectorStore, model: FakeModel):
    store.ensure_ready()

    search(store, model.embed, "what is the cap for a night in Singapore?", top_k=5)

    assert model.embed_calls[-1] == ["what is the cap for a night in Singapore?"]
