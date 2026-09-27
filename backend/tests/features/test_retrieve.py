"""F2 -- retrieve. REQ-R1, and the shape F3 builds on (REQ-R2, REQ-R3).

Offline, with the fake store and model. Whether retrieval is good enough on the
real corpus is tests/eval/, which needs the live index.
"""

from __future__ import annotations

import pytest

from app.retrieve.retrieve import Grounded, Insufficient, retrieve, search


def test_a_question_is_embedded_and_matched_against_the_passages(loaded_store, model):
    hits = search("What is the approval threshold for claims?",
                  store=loaded_store, embed=model.embed, top_k=3)

    assert model.embed_calls[-1] == ["What is the approval threshold for claims?"]
    assert hits[0].section == "4.2 Approval thresholds"


def test_search_returns_at_most_top_k_best_first(loaded_store, model):
    hits = search("client correspondence retention", store=loaded_store, embed=model.embed,
                  top_k=2)

    assert len(hits) == 2
    assert hits[0].score >= hits[1].score


def test_a_strong_match_is_grounded(loaded_store, model):
    result = retrieve("What is the approval threshold for claims?", store=loaded_store,
                      embed=model.embed, top_k=3, min_score=0.2)

    assert isinstance(result, Grounded)
    assert result.hits[0].section == "4.2 Approval thresholds"


def test_passages_below_the_threshold_are_discarded(loaded_store, model):
    result = retrieve("What is the approval threshold for claims?", store=loaded_store,
                      embed=model.embed, top_k=3, min_score=0.2)

    assert all(hit.score >= 0.2 for hit in result.hits)
    assert len(result.hits) < 3


def test_nothing_above_the_threshold_is_insufficient_not_an_empty_list(loaded_store, model):
    result = retrieve("parental leave entitlement", store=loaded_store, embed=model.embed,
                      top_k=3, min_score=0.2)

    assert isinstance(result, Insufficient)
    assert not isinstance(result, list)


def test_insufficient_reports_how_close_the_best_match_came(loaded_store, model):
    result = retrieve("approval of parental leave", store=loaded_store, embed=model.embed,
                      top_k=3, min_score=0.99)

    assert isinstance(result, Insufficient)
    assert 0 < result.best_score < 0.99


def test_a_passage_scoring_exactly_the_threshold_is_kept(loaded_store, model):
    best = search("What is the approval threshold for claims?", store=loaded_store,
                  embed=model.embed, top_k=1)[0].score

    result = retrieve("What is the approval threshold for claims?", store=loaded_store,
                      embed=model.embed, top_k=1, min_score=best)

    assert isinstance(result, Grounded)


def test_grounded_cannot_be_built_empty():
    with pytest.raises(ValueError):
        Grounded(hits=())
