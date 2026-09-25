"""Retrieval, and the refusal that is its other outcome.

The assertion this file exists for is `assert not model.was_called`. Everything
else here is scaffolding around it. If retrieval decides the corpus cannot
answer a question and the model is asked anyway, the product invents something
-- which is the failure the brief says matters most.

No network: the store is in memory and the embeddings are the fake model's.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from app.core.config import settings
from app.retrieve import service
from app.retrieve.service import retrieve
from app.retrieve.store import Grounded, Hit, Insufficient, Passage
from tests.fixtures.fake_model import FakeModel
from tests.fixtures.fake_store import FakeVectorStore

ANSWERABLE = "What is the approval threshold for a travel expense claim?"
OUT_OF_SCOPE = "How many days of paid parental leave am I entitled to?"

# The fake model hashes bags of words, so its cosine scores are on a different
# scale from a real embedding model's. These tests therefore fix their own
# threshold instead of asserting against the deployed MIN_SCORE -- which is
# tuned against the real index by scripts/tune_threshold.py, where it belongs.
TEST_MIN_SCORE = 0.15


@pytest.fixture
def wired(monkeypatch: pytest.MonkeyPatch, loaded_store: FakeVectorStore,
          model: FakeModel) -> FakeModel:
    """Point retrieval at the in-memory store and the offline model."""
    monkeypatch.setattr(service, "embed", model.embed)
    monkeypatch.setattr(service, "get_vector_store", lambda: loaded_store)
    monkeypatch.setattr(service, "settings", replace(settings, min_score=TEST_MIN_SCORE))
    return model


def _tuned(monkeypatch: pytest.MonkeyPatch, **overrides: object) -> None:
    """Change a setting for one test. Settings is frozen, so replace it."""
    monkeypatch.setattr(service, "settings", replace(settings, **overrides))


# --- grounded ---------------------------------------------------------------


def test_a_supported_question_returns_grounded_passages(wired: FakeModel) -> None:
    result = retrieve(ANSWERABLE)

    assert isinstance(result, Grounded)
    assert result.passages
    assert all(isinstance(hit, Hit) for hit in result.passages)


def test_the_expected_section_is_in_the_top_three(wired: FakeModel) -> None:
    """REQ-R5, in miniature: the right policy comes back, not just a policy."""
    result = retrieve(ANSWERABLE)

    assert isinstance(result, Grounded)
    top = result.passages[:3]
    assert any(hit.section == "4.2 Approval thresholds" for hit in top)


def test_a_grounded_result_remembers_the_question(wired: FakeModel) -> None:
    """Generation is handed the result, not the question and the result."""
    result = retrieve(ANSWERABLE)

    assert isinstance(result, Grounded)
    assert result.question == ANSWERABLE


def test_retrieval_is_limited_to_top_k(
    wired: FakeModel, monkeypatch: pytest.MonkeyPatch
) -> None:
    """REQ-R4/D3: breadth is configuration, not a number in the code."""
    _tuned(monkeypatch, retrieve_top_k=1, min_score=0.0)

    result = retrieve(ANSWERABLE)

    assert isinstance(result, Grounded)
    assert len(result.passages) == 1


# --- insufficient -----------------------------------------------------------


def test_an_out_of_scope_question_returns_insufficiency(wired: FakeModel) -> None:
    """REQ-R6. The corpus says nothing about parental leave."""
    result = retrieve(OUT_OF_SCOPE)

    assert isinstance(result, Insufficient)
    assert not isinstance(result, list)  # REQ-R3: a type, never an empty list


def test_a_refusal_never_reaches_the_model(wired: FakeModel) -> None:
    """The assertion the whole feature is judged on."""
    result = retrieve(OUT_OF_SCOPE)

    assert isinstance(result, Insufficient)
    assert not wired.was_called


def test_passages_below_the_threshold_are_discarded(
    wired: FakeModel, monkeypatch: pytest.MonkeyPatch
) -> None:
    """REQ-R2. The same question refuses once the threshold is raised."""
    assert isinstance(retrieve(ANSWERABLE), Grounded)

    _tuned(monkeypatch, min_score=0.99)

    assert isinstance(retrieve(ANSWERABLE), Insufficient)


def test_a_refusal_reports_the_score_it_rejected(
    wired: FakeModel, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D2's evidence: the near miss survives into the refusal."""
    _tuned(monkeypatch, min_score=0.99)

    result = retrieve(ANSWERABLE)

    assert isinstance(result, Insufficient)
    assert 0.0 < result.best_score < 0.99


def test_a_refusal_says_where_to_go_instead(wired: FakeModel) -> None:
    """D5. "I don't know" leaves someone where they started."""
    result = retrieve(OUT_OF_SCOPE)

    assert isinstance(result, Insufficient)
    assert len(result.reason) > 40
    assert "does not cover this" in result.reason


def test_a_refusal_names_the_team_that_owns_the_nearest_policy(
    monkeypatch: pytest.MonkeyPatch, store: FakeVectorStore, model: FakeModel
) -> None:
    """D5 again: the owner is carried on the passage, so it can be named."""
    embedding = model.embed(["Claims of 75 pounds or more require approval."])[0]
    store.upsert(
        [
            Passage(
                id="p0",
                text="Claims of 75 pounds or more require approval.",
                document_id="travel-expense-policy",
                document_title="Travel and Expense Policy",
                section="4.2 Approval thresholds",
                embedding=embedding,
                metadata={"version": "3.1", "status": "current",
                          "owner": "Group Finance"},
            )
        ]
    )
    monkeypatch.setattr(service, "embed", model.embed)
    monkeypatch.setattr(service, "get_vector_store", lambda: store)

    result = retrieve("Can I expense my partner's flight if they travel with me?")

    assert isinstance(result, Insufficient)
    assert result.owner_hint == "Group Finance"
    assert "Group Finance" in result.reason


def test_an_empty_corpus_refuses_without_a_near_miss(
    monkeypatch: pytest.MonkeyPatch, store: FakeVectorStore, model: FakeModel
) -> None:
    monkeypatch.setattr(service, "embed", model.embed)
    monkeypatch.setattr(service, "get_vector_store", lambda: store)

    result = retrieve(ANSWERABLE)

    assert isinstance(result, Insufficient)
    assert result.best_score == 0.0
    assert result.owner_hint is None
    assert not model.was_called


def test_a_blank_question_costs_nothing(
    monkeypatch: pytest.MonkeyPatch, loaded_store: FakeVectorStore, model: FakeModel
) -> None:
    """Not even an embedding call: there is nothing to embed."""
    monkeypatch.setattr(service, "embed", model.embed)
    monkeypatch.setattr(service, "get_vector_store", lambda: loaded_store)
    before = len(model.embed_calls)  # the fixture embedded the passages

    result = retrieve("   ")

    assert isinstance(result, Insufficient)
    assert len(model.embed_calls) == before
    assert not model.was_called


# --- the contract itself ----------------------------------------------------


@pytest.mark.parametrize("model_type", [Grounded, Insufficient])
def test_both_outcomes_are_immutable(model_type: type) -> None:
    """A retrieval result is a record of what happened, not a scratchpad."""
    assert model_type.__dataclass_params__.frozen  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# A follow-up is embedded WITH the turns before it.
#
# Found by deploying and asking one: "And what about above 500 pounds?" was
# refused, because on its own it carries no policy vocabulary at all. The
# answer was one row further down the table the previous question had already
# found. Retrieval still runs on every turn (REQ-C5) -- what changed is the
# text it runs on.
# ---------------------------------------------------------------------------


def test_a_follow_up_is_embedded_with_the_conversation():
    from app.retrieve.service import _contextualise

    history = [
        ("user", "What is the approval threshold for a travel expense claim?"),
        ("assistant", "Claims of 75 pounds or more require line-manager approval."),
    ]
    query = _contextualise("And what about above 500 pounds?", history)

    assert "approval threshold" in query, "the earlier question must be carried"
    assert "above 500 pounds" in query, "the current question must still be there"


def test_only_user_turns_are_carried():
    """The assistant's answer summarises passages already found.

    Carrying it would drag every query back toward those same passages, so a
    follow-up could never reach a section the first answer missed.
    """
    from app.retrieve.service import _contextualise

    history = [
        ("user", "What is the approval threshold?"),
        ("assistant", "UNIQUEANSWERTOKEN appears only here."),
    ]
    query = _contextualise("And above 500?", history)

    assert "UNIQUEANSWERTOKEN" not in query


def test_a_first_question_is_embedded_alone():
    from app.retrieve.service import _contextualise

    assert _contextualise("What is the threshold?", None) == "What is the threshold?"
    assert _contextualise("What is the threshold?", []) == "What is the threshold?"


def test_the_question_is_not_embedded_twice():
    """Callers differ on whether history already contains the current turn."""
    from app.retrieve.service import _contextualise

    query = _contextualise("Same question", [("user", "Same question")])

    assert query.count("Same question") == 1


# ---------------------------------------------------------------------------
# Superseded passages must not crowd out current ones.
#
# Found on the deployed build. Asked for the evening-meal cap, retrieval
# returned only the superseded subsistence section, and the answer was that the
# policy set does not give one -- when the current policy gives 40 pounds. A
# wrong answer, which is worse than a refusal.
#
# The two versions of the travel policy say almost the same thing, so they score
# almost the same and compete for the same slots.
# ---------------------------------------------------------------------------


def _hit(section: str, score: float, status: str):
    from app.retrieve.store import Hit

    return Hit(
        passage_id=f"{section}-{status}",
        text=section,
        document_id="travel-expense-policy",
        document_title="Travel and Expense Policy",
        section=section,
        score=score,
        metadata={"status": status, "version": "3.0" if status == "superseded" else "3.1"},
    )


def test_current_passages_are_not_displaced_by_superseded_ones():
    from app.retrieve.service import _prefer_current

    # The withdrawn version scores higher on every passage, as it really did.
    hits = [
        _hit("6.2 Subsistence", 0.71, "superseded"),
        _hit("6.1 Accommodation caps", 0.70, "superseded"),
        _hit("4.1 Approval thresholds", 0.69, "superseded"),
        _hit("6.3 Subsistence", 0.66, "current"),
        _hit("6.2 Accommodation caps", 0.65, "current"),
        _hit("4.2 Approval thresholds", 0.64, "current"),
    ]
    chosen = _prefer_current(hits, limit=4)
    statuses = [h.metadata["status"] for h in chosen]

    assert statuses.count("current") >= 3, (
        "current policy was crowded out by the withdrawn version"
    )


def test_a_superseded_passage_still_gets_through():
    """D4 shows them, flagged -- "has this changed?" stays answerable."""
    from app.retrieve.service import _prefer_current

    hits = [
        _hit("4.2 Approval thresholds", 0.73, "current"),
        _hit("2.4 Transparency", 0.70, "current"),
        _hit("3. Definitions", 0.68, "current"),
        _hit("4.1 Approval thresholds", 0.60, "superseded"),
    ]
    chosen = _prefer_current(hits, limit=4)

    assert any(h.metadata["status"] == "superseded" for h in chosen)


def test_scores_are_left_alone():
    """The threshold and the refusal evidence must still mean what they meant."""
    from app.retrieve.service import _prefer_current

    hits = [_hit("a", 0.73, "current"), _hit("b", 0.61, "superseded")]
    chosen = _prefer_current(hits, limit=2)

    assert sorted(h.score for h in chosen) == [0.61, 0.73]


def test_results_stay_in_score_order():
    from app.retrieve.service import _prefer_current

    hits = [
        _hit("a", 0.50, "current"),
        _hit("b", 0.80, "current"),
        _hit("c", 0.65, "superseded"),
    ]
    scores = [h.score for h in _prefer_current(hits, limit=3)]

    assert scores == sorted(scores, reverse=True)
