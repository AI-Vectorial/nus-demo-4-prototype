"""F3 -- refuse. REQ-R2, REQ-R3, REQ-R4, REQ-R6, and D5.

The threshold itself is tested in test_retrieve.py and, on the real corpus, in
tests/eval/. This is what the user is told when retrieval is Insufficient.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.features.refusal import policy_areas, refusal_message
from app.retrieve.retrieve import Grounded, Insufficient, retrieve

REAL_CORPUS = Path(__file__).resolve().parents[2] / "corpus"


def test_the_refusal_says_the_policy_set_does_not_cover_it():
    message = refusal_message(Insufficient(best_score=0.2), REAL_CORPUS)

    assert "does not cover" in message


def test_the_refusal_names_every_policy_area_and_its_owning_team():
    message = refusal_message(Insufficient(best_score=0.2), REAL_CORPUS)

    for title, owner in [
        ("Travel and Expense Policy", "Group Finance"),
        ("Client Onboarding and KYC Refresh Policy", "Financial Crime Compliance"),
        ("Records Retention and Data Handling Policy", "Group Legal and Company Secretariat"),
        ("Outsourcing and Third-Party Risk Policy", "Group Operational Risk"),
    ]:
        assert f"{title} — {owner}" in message


def test_the_refusal_points_anything_else_at_compliance():
    message = refusal_message(Insufficient(best_score=0.2), REAL_CORPUS)

    assert "anything else, contact Compliance" in message


def test_a_superseded_version_is_not_listed_as_a_policy_area():
    areas = policy_areas(REAL_CORPUS)

    assert len(areas) == 4
    assert len({title for title, _ in areas}) == 4


def test_the_refusal_does_not_depend_on_how_close_the_best_match_came():
    # D5: never routed to the nearest document's owner.
    near = refusal_message(Insufficient(best_score=0.50), REAL_CORPUS)
    far = refusal_message(Insufficient(best_score=None), REAL_CORPUS)

    assert near == far


def test_only_an_insufficient_retrieval_can_be_refused(loaded_store, model):
    grounded = retrieve("What is the approval threshold for claims?", store=loaded_store,
                        embed=model.embed, top_k=3, min_score=0.2)
    assert isinstance(grounded, Grounded)

    with pytest.raises(TypeError):
        refusal_message(grounded, REAL_CORPUS)  # type: ignore[arg-type]


def test_refusing_makes_no_model_call(loaded_store, model):
    result = retrieve("parental leave entitlement", store=loaded_store, embed=model.embed,
                      top_k=3, min_score=0.2)

    refusal_message(result, REAL_CORPUS)

    assert not model.was_called
