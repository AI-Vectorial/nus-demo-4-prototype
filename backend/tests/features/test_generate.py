"""F4 -- generate. REQ-G1 .. REQ-G6, NFR-3.

Uses the fake model only. No network. The live check is a separate run.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import app.generate.compose as compose_module
from app.core.config import settings
from app.generate.compose import (
    PROMPT_PATH,
    PROMPT_VERSION,
    Answered,
    Degraded,
    compose,
)
from app.retrieve.search import Grounded
from app.retrieve.store import Hit

QUESTION = "What is the approval threshold for a travel expense claim?"


def _hit(text: str, section: str = "4.2 Approval thresholds",
         status: str = "current", version: str = "3.1") -> Hit:
    return Hit(
        passage_id=f"id-{section}-{version}",
        text=text,
        document_id="travel-expense-policy",
        document_title="Travel and Expense Policy",
        section=section,
        score=0.8,
        metadata={"version": version, "status": status},
    )


def test_the_prompt_is_a_versioned_file_not_a_literal():
    """REQ-G4: the prompt lives in a file, and its version is that file's name."""
    assert PROMPT_PATH.is_file()
    assert PROMPT_PATH.name == f"{PROMPT_VERSION}.md"
    assert "{passages}" in PROMPT_PATH.read_text(encoding="utf-8")


def test_an_answer_is_composed_from_the_passages_given(model):
    """REQ-G1, REQ-G2: the only context the model receives is the passages."""
    hit = _hit("Claims of 75 pounds or more require line-manager approval.")

    result = compose(QUESTION, Grounded(hits=[hit]), model.generate, enabled=True)

    assert isinstance(result, Answered)
    assert model.was_called
    prompt = model.generate_calls[-1]["prompt"]
    assert hit.text in prompt
    assert QUESTION in prompt


def test_the_answer_carries_the_passages_that_produced_it(model):
    """REQ-G3."""
    hits = [_hit("Claims of 75 pounds or more.", section="4.2 Approval thresholds")]

    result = compose(QUESTION, Grounded(hits=hits), model.generate, enabled=True)

    assert isinstance(result, Answered)
    assert result.hits == hits


def test_every_answer_records_prompt_version_model_and_latency(model):
    """REQ-G5."""
    result = compose(QUESTION, Grounded(hits=[_hit("text")]), model.generate, enabled=True)

    assert isinstance(result, Answered)
    assert result.prompt_version == PROMPT_VERSION
    assert result.model == settings.llm_model
    assert result.latency_ms >= 0


def test_generation_disabled_returns_passages_with_no_model_call(model, monkeypatch):
    """REQ-G6, NFR-3: GENERATION_ENABLED=false leaves a working search behind."""
    monkeypatch.setattr(compose_module, "settings", replace(settings, generation_enabled=False))
    hits = [_hit("Claims of 75 pounds or more.")]

    result = compose(QUESTION, Grounded(hits=hits), model.generate)

    assert isinstance(result, Degraded)
    assert result.hits == hits
    assert not model.was_called


def test_an_unreachable_provider_degrades_with_passages(failing_model):
    """REQ-G6, REQ-U6: the provider fails, so passages come back with no answer."""
    hits = [_hit("Claims of 75 pounds or more.")]

    result = compose(QUESTION, Grounded(hits=hits), failing_model.generate, enabled=True)

    assert isinstance(result, Degraded)
    assert result.hits == hits
    assert "fake" in result.reason


def test_a_superseded_source_is_named_in_the_notice(model):
    """D4: an answer resting on a superseded version says so."""
    old = _hit("Claims of 50 pounds or more.", version="3.0", status="superseded")

    result = compose(QUESTION, Grounded(hits=[old]), model.generate, enabled=True)

    assert isinstance(result, Answered)
    assert result.notice is not None
    assert "superseded" in result.notice.lower()


def test_a_current_only_answer_has_no_notice(model):
    result = compose(QUESTION, Grounded(hits=[_hit("text")]), model.generate, enabled=True)

    assert isinstance(result, Answered)
    assert result.notice is None


def test_superseded_passages_are_labelled_in_the_prompt(model):
    """The model sees each passage's status, so it can say which version it used."""
    old = _hit("Claims of 50 pounds or more.", version="3.0", status="superseded")

    compose(QUESTION, Grounded(hits=[old]), model.generate, enabled=True)

    assert "superseded" in model.generate_calls[-1]["prompt"]


def test_conflicting_policies_are_both_passed_to_the_model(model):
    """D6: two conflicting passages go to the model together, and the prompt
    tells it to surface the conflict rather than pick one."""
    retention = _hit("Keep for seven years.", section="4.1 General table")
    retention.metadata.update(version="4.0")
    outsourcing = Hit(
        passage_id="o1",
        text="Destroy within five years of termination.",
        document_id="outsourcing-third-party",
        document_title="Outsourcing",
        section="6.4 Return and destruction on exit",
        score=0.6,
        metadata={"version": "1.8", "status": "current"},
    )

    compose("How long can they keep it?", Grounded(hits=[retention, outsourcing]),
            model.generate, enabled=True)

    prompt = model.generate_calls[-1]["prompt"]
    assert "seven years" in prompt and "five years" in prompt
    assert "conflict" in PROMPT_PATH.read_text(encoding="utf-8").lower()


def test_no_provider_sdk_is_imported_outside_the_client():
    """The provider boundary stays where it is: compose uses generate(), not the SDK."""
    source = Path(compose_module.__file__).read_text(encoding="utf-8")
    assert "openai" not in source
