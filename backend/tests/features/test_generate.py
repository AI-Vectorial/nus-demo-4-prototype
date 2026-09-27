"""F4 -- generate. REQ-G1 .. REQ-G6, D4, D6.

compose() takes only a Grounded retrieval. It either returns an Answered built
from those passages, or -- with the kill switch off, or the provider down -- a
Degraded carrying the same passages and no answer.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from app.generate.answer import (
    PROMPT_VERSION,
    Answered,
    Degraded,
    compose,
    system_prompt,
)
from app.retrieve.retrieve import Grounded, Insufficient, retrieve

QUESTION = "What is the approval threshold for claims?"


@pytest.fixture
def grounded(loaded_store, model) -> Grounded:
    result = retrieve(QUESTION, store=loaded_store, embed=model.embed, top_k=3, min_score=0.1)
    assert isinstance(result, Grounded)
    return result


def test_an_answer_is_composed_from_the_retrieved_passages(grounded, model):
    result = compose(QUESTION, grounded, generate=model.generate, model_name="m", enabled=True)

    assert isinstance(result, Answered)
    assert result.text == model.answer
    prompt = model.generate_calls[-1]["prompt"]
    for hit in grounded.hits:
        assert hit.text in prompt
    assert QUESTION in prompt


def test_the_answer_carries_exactly_the_passages_that_produced_it(grounded, model):
    result = compose(QUESTION, grounded, generate=model.generate, model_name="m", enabled=True)

    assert result.hits == grounded.hits


def test_the_model_is_told_to_answer_only_from_the_passages(grounded, model):
    compose(QUESTION, grounded, generate=model.generate, model_name="m", enabled=True)

    system = model.generate_calls[-1]["system"]
    assert system == system_prompt()
    assert "only" in system.lower() and "passages" in system.lower()


def test_the_prompt_lives_in_a_versioned_file():
    from app.generate import answer

    path = answer.PROMPT_DIR / f"{PROMPT_VERSION}.md"
    assert path.is_file()
    assert system_prompt() == path.read_text(encoding="utf-8").strip()


def test_every_answer_records_prompt_version_model_and_latency(grounded, model):
    result = compose(QUESTION, grounded, generate=model.generate,
                     model_name="openai/test-model", enabled=True)

    assert result.prompt_version == PROMPT_VERSION
    assert result.model == "openai/test-model"
    assert isinstance(result.latency_ms, int) and result.latency_ms >= 0


def test_a_superseded_passage_is_labelled_superseded_in_the_prompt(grounded, model):
    old = replace(grounded.hits[0], metadata={"version": "3.0", "status": "superseded"})
    compose(QUESTION, Grounded((old, *grounded.hits[1:])), generate=model.generate,
            model_name="m", enabled=True)

    assert "SUPERSEDED" in model.generate_calls[-1]["prompt"]


def test_the_prompt_tells_the_model_the_current_version_governs():
    # D4: shown, flagged -- never answered from as if it were current.
    assert "current version governs" in system_prompt().lower()


def test_the_prompt_tells_the_model_to_surface_a_conflict_not_resolve_it():
    # D6.
    system = system_prompt().lower()
    assert "conflict" in system
    assert "do not choose" in system


# --- the kill switch: REQ-G6 -------------------------------------------------


def test_generation_off_returns_the_passages_with_no_answer_and_no_model_call(grounded, model):
    result = compose(QUESTION, grounded, generate=model.generate, model_name="m", enabled=False)

    assert isinstance(result, Degraded)
    assert result.hits == grounded.hits
    assert not model.was_called


def test_an_unreachable_provider_returns_the_passages_with_no_answer(grounded, failing_model):
    result = compose(QUESTION, grounded, generate=failing_model.generate, model_name="m",
                     enabled=True)

    assert isinstance(result, Degraded)
    assert result.hits == grounded.hits
    assert "unreachable" in result.reason


def test_an_insufficient_retrieval_cannot_be_composed(model):
    with pytest.raises(TypeError):
        compose(QUESTION, Insufficient(best_score=0.1),  # type: ignore[arg-type]
                generate=model.generate, model_name="m", enabled=True)

    assert not model.was_called
