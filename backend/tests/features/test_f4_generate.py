"""F4 -- generate. Epic criteria 13 to 19 (20 is a manual check at stage 06).

answer_question() is the whole question-to-outcome path without the database:
retrieve, then refuse, compose or degrade.
"""

from __future__ import annotations

import ast
from pathlib import Path

from app.core.config import settings
from app.features.ask import Answered, Degraded, Refused, answer_question
from app.generate.prompt import load_prompt, refusal_text

APP = Path(__file__).resolve().parents[2] / "app"
QUESTION = "What is the approval threshold for expenses?"
OFF_TOPIC = "something entirely unrelated to banking policy"


def _ask(store, model, question=QUESTION, *, enabled=True, min_score=0.1):
    return answer_question(question, store, model.embed, model.generate,
                           generation_enabled=enabled, min_score=min_score)


# --------------------------------------------------------------- criterion 13


def test_every_citation_is_a_retrieved_passage(loaded_store, model):
    """REQ-G1, REQ-G3."""
    retrieved = {(p.document_id, p.section, p.metadata["version"])
                 for p in loaded_store._passages.values()}

    outcome = _ask(loaded_store, model)

    assert isinstance(outcome, Answered)
    assert outcome.citations
    assert {(c.document_id, c.section, c.metadata["version"])
            for c in outcome.citations} <= retrieved


def test_citations_are_one_per_passage_without_duplicates(store, model, passages):
    """D7 -- the same document, section and version is cited once."""
    twin = passages[0].__class__(**{**passages[0].__dict__, "id": "twin"})
    store.upsert([*passages, twin])

    outcome = _ask(store, model)

    keys = [(c.document_id, c.section, c.metadata["version"]) for c in outcome.citations]
    assert len(keys) == len(set(keys))


# --------------------------------------------------------------- criterion 14


def test_the_model_sees_only_the_question_and_the_retrieved_passages(loaded_store, model):
    """REQ-G1, REQ-G2."""
    _ask(loaded_store, model)
    [call] = model.generate_calls
    sent = call["prompt"]

    assert QUESTION in sent
    assert "Claims of 75 pounds or more" in sent
    # The passages that did not clear the threshold never reach the model.
    assert "twelve months" not in sent
    assert "only" in call["system"].lower()


def test_superseded_and_conflicting_passages_are_instructed(loaded_store, model):
    """D4, D6 -- the instructions are in the prompt, not decided in code."""
    _ask(loaded_store, model)
    system = model.generate_calls[0]["system"].lower()

    assert "superseded" in system
    assert "conflict" in system


# --------------------------------------------------------------- criterion 15


def test_the_prompt_lives_in_a_versioned_file():
    """REQ-G4."""
    prompt = load_prompt()

    assert prompt.path.parent.parent == APP / "generate"
    assert prompt.version
    assert prompt.version in prompt.path.read_text(encoding="utf-8")


def test_no_prompt_text_is_a_python_string_literal():
    """REQ-G4 -- the instruction wording appears in no .py file."""
    wording = load_prompt().system.splitlines()[0]
    for path in APP.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert wording not in node.value, path


# --------------------------------------------------------------- criterion 16


def test_an_answer_records_its_model_and_prompt_version(loaded_store, model):
    """REQ-G5 -- latency_ms is added and stored by /ask, criterion 16 in F5."""
    outcome = _ask(loaded_store, model)

    assert outcome.model == settings.llm_model
    assert outcome.prompt_version == load_prompt().version


# --------------------------------------------------------------- criterion 17


def test_the_kill_switch_returns_passages_and_no_answer(loaded_store, model):
    """REQ-G6 -- GENERATION_ENABLED=false."""
    outcome = _ask(loaded_store, model, enabled=False)

    assert isinstance(outcome, Degraded)
    assert outcome.citations
    assert not model.was_called


def test_the_kill_switch_defaults_to_configuration(loaded_store, model):
    outcome = answer_question(QUESTION, loaded_store, model.embed, model.generate,
                              min_score=0.1)
    expected = Answered if settings.generation_enabled else Degraded
    assert isinstance(outcome, expected)


# --------------------------------------------------------------- criterion 18


def test_an_unreachable_model_degrades_instead_of_failing(loaded_store, model):
    """REQ-G6 -- ProviderError from the model becomes a degraded outcome."""
    model.fail_after = len(model.embed_calls) + 1  # embedding works, generation fails

    outcome = _ask(loaded_store, model)

    assert isinstance(outcome, Degraded)
    assert outcome.citations
    assert model.generate_calls


def test_an_empty_model_reply_degrades_instead_of_answering(loaded_store, model):
    """Review F3 -- an empty answer box is not an answer."""
    model.answer = "   "

    outcome = _ask(loaded_store, model)

    assert isinstance(outcome, Degraded)
    assert outcome.citations


# --------------------------------------------------------------- criterion 19


def test_off_topic_with_generation_off_is_refused_not_degraded(loaded_store, model):
    """REQ-R3, REQ-G6 -- nothing retrieved means nothing to degrade to."""
    outcome = _ask(loaded_store, model, OFF_TOPIC, enabled=False, min_score=0.99)

    assert isinstance(outcome, Refused)
    assert not model.was_called


def test_off_topic_with_generation_on_is_refused_without_a_model_call(loaded_store, model):
    """REQ-R3, NFR-2 -- criterion 10 on the full path."""
    outcome = _ask(loaded_store, model, OFF_TOPIC, min_score=0.99)

    assert isinstance(outcome, Refused)
    assert not model.was_called


def test_a_refusal_says_where_to_go(loaded_store, model):
    """D5 -- the covered areas, their owners, and Compliance for the rest."""
    outcome = _ask(loaded_store, model, OFF_TOPIC, min_score=0.99)

    assert outcome.text == refusal_text()
    for expected in ("Travel and Expense Policy", "Group Finance", "Compliance"):
        assert expected in outcome.text
    assert "3.0" not in outcome.text  # the superseded version is not an area to consult
