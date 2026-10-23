"""F3 -- refuse. REQ-R2, REQ-R3, REQ-R4, REQ-R6.

The threshold value is a team decision (D2). These tests pass an explicit
threshold, or set one through settings, so they do not depend on the value.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

import app.retrieve.search as search_module
from app.core.config import settings
from app.retrieve.search import Grounded, Insufficient, retrieve_grounded

APPROVAL = "What is the approval threshold for a travel expense claim?"
UNRELATED = "something entirely unrelated to banking policy"


def test_passages_below_the_threshold_are_discarded(loaded_store, model):
    """REQ-R2: nothing scores above 0.99, so nothing survives."""
    outcome = retrieve_grounded(UNRELATED, loaded_store, model.embed, min_score=0.99)

    assert isinstance(outcome, Insufficient)


def test_a_strong_match_is_grounded(loaded_store, model):
    """REQ-R3: a question with a real match returns passages, not a refusal."""
    outcome = retrieve_grounded(APPROVAL, loaded_store, model.embed, min_score=0.1)

    assert isinstance(outcome, Grounded)
    assert outcome.hits
    assert all(hit.score >= 0.1 for hit in outcome.hits)


def test_insufficiency_is_explicit_never_an_empty_grounded(loaded_store, model):
    """REQ-R3: a refusal is its own type. An empty Grounded cannot be built."""
    outcome = retrieve_grounded(UNRELATED, loaded_store, model.embed, min_score=0.99)

    assert not isinstance(outcome, Grounded)
    assert isinstance(outcome, Insufficient)
    assert outcome.reason


def test_a_refusal_does_not_call_the_model(loaded_store, model):
    """REQ-R3 and REQ-G2: retrieval refuses without any generation call."""
    retrieve_grounded(UNRELATED, loaded_store, model.embed, min_score=0.99)

    assert not model.was_called


def test_threshold_is_read_from_settings(loaded_store, model, monkeypatch):
    """REQ-R4: the value comes from configuration, not a literal in code."""
    monkeypatch.setattr(search_module, "settings", replace(settings, min_score=0.99))

    outcome = retrieve_grounded(APPROVAL, loaded_store, model.embed)

    assert isinstance(outcome, Insufficient)


def test_refusing_to_run_without_a_threshold(loaded_store, model, monkeypatch):
    """REQ-R4: no threshold configured is an error, not a silent default."""
    monkeypatch.setattr(search_module, "settings", replace(settings, min_score=None))

    with pytest.raises(ValueError, match="MIN_SCORE"):
        retrieve_grounded(APPROVAL, loaded_store, model.embed)


def test_an_explicit_threshold_overrides_settings(loaded_store, model, monkeypatch):
    monkeypatch.setattr(search_module, "settings", replace(settings, min_score=0.99))

    outcome = retrieve_grounded(APPROVAL, loaded_store, model.embed, min_score=0.1)

    assert isinstance(outcome, Grounded)
