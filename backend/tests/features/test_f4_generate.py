"""F4 -- generate. Criteria C8 and the prompt behind C30 / D4 / D6.

Whether the real model surfaces the Q10 conflict well (C30's wording) is read on
the live answer; that both sections are cited is tested in test_f5_ask.py.
"""

from __future__ import annotations

import pytest

from app.features.context import Turn
from app.generate.answer import PROMPT_VERSION, Answered, Degraded, compose, render
from app.retrieve.retrieve import Grounded, Insufficient
from app.retrieve.store import Hit


def hit(section: str, text: str, version: str = "3.1", status: str = "current",
        document_id: str = "travel-expense-policy",
        title: str = "Travel and Expense Policy") -> Hit:
    return Hit(passage_id=section, text=text, document_id=document_id, document_title=title,
               section=section, score=0.8, metadata={"version": version, "status": status})


GROUNDED = Grounded((
    hit("4.2 Approval thresholds", "Claims of £75 or more require line-manager approval."),
    hit("4.1 Approval thresholds", "Claims of £50 or more require approval.",
        version="3.0", status="superseded"),
))


def test_an_answer_is_composed_from_the_passages(model):
    result = compose("What is the threshold?", [], GROUNDED, model.generate,
                     enabled=True, model_name="m")

    assert isinstance(result, Answered)
    prompt = model.generate_calls[0]["prompt"]
    assert "Claims of £75 or more" in prompt and "Claims of £50 or more" in prompt


def test_an_answer_records_its_prompt_version_and_model(model):
    result = compose("q", [], GROUNDED, model.generate, enabled=True, model_name="the-model")

    assert result.prompt_version == PROMPT_VERSION == "answer-v1"
    assert result.model == "the-model"


def test_c8_the_kill_switch_degrades_without_calling_the_model(model):
    result = compose("q", [], GROUNDED, model.generate, enabled=False, model_name="m")

    assert isinstance(result, Degraded)
    assert not model.was_called


def test_c8_an_unreachable_provider_degrades(failing_model):
    result = compose("q", [], GROUNDED, failing_model.generate, enabled=True, model_name="m")

    assert isinstance(result, Degraded)


def test_insufficient_retrieval_cannot_reach_the_model(model):
    with pytest.raises(TypeError):
        compose("q", [], Insufficient(), model.generate, enabled=True, model_name="m")
    assert not model.was_called


def test_d4_superseded_passages_are_labelled_as_superseded():
    system, prompt = render("q", [], GROUNDED)

    assert "v3.0, SUPERSEDED" in prompt
    assert "v3.1, current" in prompt
    assert "current version governs" in system


def test_d6_the_prompt_says_to_surface_a_conflict_and_not_resolve_it():
    system, _ = render("q", [], GROUNDED)

    assert "do not choose between them" in system
    assert "escalation route" in system


def test_d8_earlier_messages_are_context_not_evidence():
    history = [Turn("user", "What is the travel limit?"), Turn("assistant", "£75.")]
    system, prompt = render("And above that?", history, GROUNDED)

    assert "User: What is the travel limit?" in prompt
    assert "Assistant: £75." in prompt
    assert "not evidence" in system


def test_the_prompt_is_read_from_a_versioned_file():
    system, _ = render("q", [], GROUNDED)

    assert system.startswith("You answer questions from staff at Aldermere Bank")
