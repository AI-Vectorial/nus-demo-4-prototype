"""F2 -- retrieve. REQ-R1, REQ-R5.

The fake-model tests prove the mechanism. The real check, Q1-Q10 on the live
index with real embeddings, is `python -m app.retrieve.evaluate`.
"""

from __future__ import annotations

from app.core.config import settings
from app.retrieve.evaluate import (
    ANSWERABLE,
    TOP_CHECK,
    UNANSWERABLE,
    satisfied,
)
from app.retrieve.search import retrieve
from app.retrieve.store import Hit

TRAVEL = "travel-expense-policy"


def _hit(document_id: str, version: str, section: str) -> Hit:
    return Hit(
        passage_id="x",
        text="t",
        document_id=document_id,
        document_title="T",
        section=section,
        score=0.9,
        metadata={"version": version, "status": "current"},
    )


def test_retrieve_embeds_the_question_and_returns_the_best_match_first(loaded_store, model):
    """REQ-R1: the question is embedded and matched against the store."""
    hits = retrieve("What is the approval threshold?", loaded_store, model.embed)

    assert hits
    assert hits[0].document_id == TRAVEL
    assert model.embed_calls[-1] == ["What is the approval threshold?"]


def test_retrieve_honours_an_explicit_limit(loaded_store, model):
    hits = retrieve("approval threshold", loaded_store, model.embed, limit=1)

    assert len(hits) == 1


def test_retrieve_defaults_to_the_configured_top_k(loaded_store, model):
    """The count comes from RETRIEVE_TOP_K, not a literal in code."""
    hits = retrieve("approval threshold", loaded_store, model.embed)

    assert len(hits) == min(settings.retrieve_top_k, loaded_store.count())


def test_a_match_needs_the_current_version_of_the_section():
    """A superseded v3.0 section with the same heading does not satisfy Q1."""
    requirement = [[(TRAVEL, "3.1", "4.2 Approval thresholds")]]

    assert satisfied([_hit(TRAVEL, "3.1", "4.2 Approval thresholds")], requirement)
    assert not satisfied([_hit(TRAVEL, "3.0", "4.2 Approval thresholds")], requirement)


def test_only_the_top_three_count_toward_a_pass():
    """EVALUATION.md: the expected section must appear in the top three."""
    requirement = [[(TRAVEL, "3.1", "4.2 Approval thresholds")]]
    hits = [
        _hit(TRAVEL, "3.1", "1. Purpose"),
        _hit(TRAVEL, "3.1", "2. Principles"),
        _hit(TRAVEL, "3.1", "3. Scope"),
        _hit(TRAVEL, "3.1", "4.2 Approval thresholds"),
    ]

    assert TOP_CHECK == 3
    assert not satisfied(hits, requirement)


def test_the_evaluation_set_has_ten_answerable_and_three_unanswerable_questions():
    """Transcribed from corpus/EVALUATION.md. Q10 needs two documents."""
    assert len(ANSWERABLE) == 10
    assert len(UNANSWERABLE) == 3
    q10 = ANSWERABLE[-1]
    assert len(q10[1]) == 2
