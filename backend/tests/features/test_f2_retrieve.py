"""F2 -- retrieve. REQ-R1..R4, the D9 query text, and the retrieval half of C4.

The evaluation questions themselves (C4, C5) need the real embedding model and
run through `python -m app.retrieve.evaluate`; the results are in
docs/design/D2-refusal-threshold.md.
"""

from __future__ import annotations

import pytest

from app.features.context import Turn, retrieval_questions, window
from app.retrieve.retrieve import Grounded, Insufficient, query_text, retrieve


def test_a_match_above_the_threshold_is_grounded(loaded_store, model):
    result = retrieve("approval threshold claims", loaded_store, model.embed,
                      top_k=5, min_score=0.1)

    assert isinstance(result, Grounded)
    assert result.hits[0].section == "4.2 Approval thresholds"


def test_nothing_above_the_threshold_is_insufficient_not_an_empty_list(loaded_store, model):
    result = retrieve("parental leave entitlement", loaded_store, model.embed,
                      top_k=5, min_score=0.1)

    assert isinstance(result, Insufficient)
    assert not hasattr(result, "hits")


def test_every_passage_below_the_threshold_is_discarded(loaded_store, model):
    result = retrieve("approval threshold claims", loaded_store, model.embed,
                      top_k=5, min_score=0.1)

    assert all(hit.score >= 0.1 for hit in result.hits)
    assert len(result.hits) < loaded_store.count()


def test_top_k_is_a_ceiling(loaded_store, model):
    result = retrieve("claims retained refreshed", loaded_store, model.embed,
                      top_k=1, min_score=0.0)

    assert len(result.hits) == 1


def test_a_grounded_result_cannot_be_empty():
    with pytest.raises(ValueError):
        Grounded(hits=())


def test_query_text_is_the_questions_in_order():
    assert query_text(["first?", "second?"]) == "first?\nsecond?"


# --- D9: the user questions within the last CONTEXT_MESSAGES messages ----------

HISTORY = [
    Turn("user", "Q1"), Turn("assistant", "A1"),
    Turn("user", "Q2"), Turn("assistant", "A2"),
    Turn("user", "Q3"), Turn("assistant", "A3"),
]


def test_the_window_counts_messages_and_includes_the_current_question():
    assert window(HISTORY, "Q4", size=5) == [
        Turn("user", "Q2"), Turn("assistant", "A2"),
        Turn("user", "Q3"), Turn("assistant", "A3"),
        Turn("user", "Q4"),
    ]


def test_retrieval_runs_on_the_user_questions_in_the_window_only():
    assert retrieval_questions(window(HISTORY, "Q4", size=5)) == ["Q2", "Q3", "Q4"]


def test_a_first_question_retrieves_on_itself():
    assert retrieval_questions(window([], "Q1", size=5)) == ["Q1"]


def test_assistant_answers_never_reach_the_retrieval_text():
    text = query_text(retrieval_questions(window(HISTORY, "Q4", size=5)))
    assert "A2" not in text and "A3" not in text
