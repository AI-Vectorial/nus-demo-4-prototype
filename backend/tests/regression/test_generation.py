"""Generation: composed from the passages, and honest when it cannot be.

Two behaviours are worth more than the rest. An answer must be built only from
what retrieval found (REQ-G1, REQ-G2), and the product must survive the model
being switched off or unreachable (REQ-G6) -- returning passages with no
answer rather than an exception.

No network: the model is the offline fake, wired in with monkeypatch.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from app.core.config import settings
from app.generate import service
from app.generate.service import Answer, answer, prompt_text
from app.retrieve.store import Grounded, Hit
from tests.fixtures.fake_model import FakeModel

APPROVAL = Hit(
    passage_id="p0",
    text="Claims of 75 pounds or more require line-manager approval.",
    document_id="travel-expense-policy",
    document_title="Travel and Expense Policy",
    section="4.2 Approval thresholds",
    score=0.81,
    metadata={"version": "3.1", "status": "current", "owner": "Group Finance"},
)

# Same document and section, lower score: D7 says these are one citation.
APPROVAL_AGAIN = replace(APPROVAL, passage_id="p1", score=0.62,
                         text="Thresholds are inclusive of the stated amount.")

WITHDRAWN = replace(
    APPROVAL,
    passage_id="p2",
    text="Claims of 50 pounds or more require line-manager approval.",
    section="4.2 Approval thresholds (v3.0)",
    score=0.55,
    metadata={"version": "3.0", "status": "superseded", "owner": "Group Finance"},
)

QUESTION = "What is the approval threshold for a travel expense claim?"


@pytest.fixture
def grounded() -> Grounded:
    return Grounded(passages=[APPROVAL, WITHDRAWN], question=QUESTION)


@pytest.fixture
def wired(monkeypatch: pytest.MonkeyPatch, model: FakeModel) -> FakeModel:
    """Point generation at the offline model."""
    monkeypatch.setattr(service, "generate", model.generate)
    return model


def _tuned(monkeypatch: pytest.MonkeyPatch, **overrides: object) -> None:
    """Change a setting for one test. Settings is frozen, so replace it."""
    monkeypatch.setattr(service, "settings", replace(settings, **overrides))


def _prompt(model: FakeModel) -> str:
    assert model.generate_calls, "the model was never called"
    return model.generate_calls[-1]["prompt"]


# --- composing an answer ----------------------------------------------------


def test_an_answer_is_composed_and_not_degraded(
    wired: FakeModel, grounded: Grounded
) -> None:
    result = answer(grounded)

    assert isinstance(result, Answer)
    assert result.text == wired.answer
    assert result.degraded is False


def test_the_prompt_carries_the_passages_and_the_question(
    wired: FakeModel, grounded: Grounded
) -> None:
    """REQ-G1: the model is given the passages, not asked to recall policy."""
    answer(grounded)
    prompt = _prompt(wired)

    assert APPROVAL.text in prompt
    assert "4.2 Approval thresholds" in prompt
    assert QUESTION in prompt


def test_the_versioned_prompt_file_is_the_system_message(
    wired: FakeModel, grounded: Grounded
) -> None:
    """REQ-G4. The instructions are a file, not a literal in this module."""
    answer(grounded)

    assert wired.generate_calls[-1]["system"] == prompt_text()


def test_a_superseded_passage_is_labelled_in_the_prompt(
    wired: FakeModel, grounded: Grounded
) -> None:
    """D4: shown and flagged. The model cannot flag what it is not told."""
    answer(grounded)

    assert "SUPERSEDED" in _prompt(wired)


def test_every_answer_records_how_it_was_produced(
    wired: FakeModel, grounded: Grounded
) -> None:
    """REQ-G5."""
    result = answer(grounded)

    assert result.prompt_version == "answer.v1"
    assert result.model == settings.llm_model
    assert result.latency_ms >= 0


# --- citations --------------------------------------------------------------


def test_citations_are_one_per_section_keeping_the_best_score(
    wired: FakeModel
) -> None:
    """D7. Two passages from 4.2 are one citation, at the higher score."""
    result = answer(Grounded(passages=[APPROVAL_AGAIN, APPROVAL], question=QUESTION))

    assert len(result.citations) == 1
    assert result.citations[0].score == APPROVAL.score


def test_different_sections_stay_separate(wired: FakeModel, grounded: Grounded) -> None:
    result = answer(grounded)

    sections = [citation.section for citation in result.citations]
    assert sections == [APPROVAL.section, WITHDRAWN.section]


def test_a_citation_carries_what_a_reader_needs_to_check_it(
    wired: FakeModel, grounded: Grounded
) -> None:
    """REQ-U3: document, section, version and status -- not just a title."""
    citation = answer(grounded).citations[0]

    assert citation.document_id == "travel-expense-policy"
    assert citation.document_title == "Travel and Expense Policy"
    assert citation.section == "4.2 Approval thresholds"
    assert citation.version == "3.1"
    assert citation.status == "current"


def test_a_superseded_citation_says_so(wired: FakeModel, grounded: Grounded) -> None:
    """REQ-U4 needs the status to survive as far as the response."""
    statuses = {citation.status for citation in answer(grounded).citations}

    assert "superseded" in statuses


# --- conversation -----------------------------------------------------------


def test_recent_turns_are_given_to_the_model(
    wired: FakeModel, grounded: Grounded
) -> None:
    """REQ-C3: a follow-up is answered with the conversation in context."""
    history = [
        ("user", "What is the approval threshold?"),
        ("assistant", "Claims of 75 pounds or more need line-manager approval."),
    ]

    answer(grounded, history)
    prompt = _prompt(wired)

    assert "What is the approval threshold?" in prompt
    assert "Claims of 75 pounds or more need line-manager approval." in prompt


def test_history_is_trimmed_to_context_messages(
    wired: FakeModel, grounded: Grounded, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D8/REQ-C4: how much a follow-up sees is configuration, not a constant."""
    _tuned(monkeypatch, context_messages=2)
    history = [("user", f"turn {n}") for n in range(6)]

    answer(grounded, history)
    prompt = _prompt(wired)

    assert "turn 5" in prompt
    assert "turn 4" in prompt
    assert "turn 0" not in prompt


def test_no_history_means_no_conversation_section(
    wired: FakeModel, grounded: Grounded
) -> None:
    answer(grounded)

    assert "Earlier in this conversation" not in _prompt(wired)


# --- the kill switch, REQ-G6 ------------------------------------------------


def test_an_unreachable_provider_degrades_instead_of_raising(
    monkeypatch: pytest.MonkeyPatch, failing_model: FakeModel, grounded: Grounded
) -> None:
    """The passages are still worth having. An exception is not."""
    monkeypatch.setattr(service, "generate", failing_model.generate)

    result = answer(grounded)

    assert result.degraded is True
    assert result.text is None
    assert result.citations, "degraded mode must still return the passages"


def test_generation_disabled_never_calls_the_model(
    wired: FakeModel, grounded: Grounded, monkeypatch: pytest.MonkeyPatch
) -> None:
    """GENERATION_ENABLED=false leaves a working policy search behind."""
    _tuned(monkeypatch, generation_enabled=False)

    result = answer(grounded)

    assert result.degraded is True
    assert result.text is None
    assert result.citations
    assert not wired.was_called


def test_an_empty_answer_is_treated_as_a_failure(
    monkeypatch: pytest.MonkeyPatch, grounded: Grounded
) -> None:
    """Blank text renders as an answer that says nothing. Degraded is honest."""
    monkeypatch.setattr(service, "generate", FakeModel(answer="   ").generate)

    result = answer(grounded)

    assert result.degraded is True
    assert result.text is None


def test_a_degraded_answer_still_records_its_provenance(
    monkeypatch: pytest.MonkeyPatch, failing_model: FakeModel, grounded: Grounded
) -> None:
    monkeypatch.setattr(service, "generate", failing_model.generate)

    result = answer(grounded)

    assert result.prompt_version == "answer.v1"
    assert result.model == settings.llm_model
    assert result.latency_ms >= 0


# --- the prompt itself ------------------------------------------------------


def test_the_prompt_forbids_answering_from_outside_the_passages() -> None:
    """REQ-G2. The rule is in the file, so a reviewer can read it."""
    text = prompt_text().lower()

    assert "only from the supplied passages" in text
    assert "general knowledge" in text


def test_the_prompt_refuses_to_resolve_a_conflict() -> None:
    """D6. Deciding which policy wins is not the software's call."""
    text = prompt_text().lower()

    assert "conflict" in text
    assert "do not decide which one wins" in text


def test_the_prompt_prefers_the_current_version() -> None:
    """D4. Superseded is shown, flagged, and not answered from silently."""
    text = prompt_text().lower()

    assert "superseded" in text
    assert "answer from the current passage" in text
