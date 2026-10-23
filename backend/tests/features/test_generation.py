from __future__ import annotations

from app.features.answer import Answered, Degraded, generate_answer


def test_answer_uses_given_passages_and_records_prompt_metadata(passages, model) -> None:
    result = generate_answer(
        "What is the approval threshold?",
        passages,
        generate_text=model.generate,
        enabled=True,
        model_name="test-model",
    )

    assert isinstance(result, Answered)
    assert result.answer == model.answer
    assert result.citations == passages
    assert result.prompt_version
    assert result.model == "test-model"
    assert result.latency_ms >= 0
    assert "Claims of 75 pounds or more" in model.generate_calls[0]["prompt"]


def test_disabled_generation_returns_passages_without_calling_model(passages, model) -> None:
    result = generate_answer(
        "What is the approval threshold?",
        passages,
        generate_text=model.generate,
        enabled=False,
        model_name="test-model",
    )

    assert isinstance(result, Degraded)
    assert result.answer is None
    assert result.citations == passages
    assert model.generate_calls == []


def test_provider_failure_returns_degraded_passages(passages, failing_model) -> None:
    def fail_generation(prompt: str, *, system: str | None = None) -> str:
        return failing_model.generate(prompt, system=system)

    result = generate_answer(
        "What is the approval threshold?",
        passages,
        generate_text=fail_generation,
        enabled=True,
        model_name="test-model",
    )

    assert isinstance(result, Degraded)
    assert result.answer is None
    assert result.citations == passages
    assert len(failing_model.generate_calls) == 1


def test_generation_rejects_empty_evidence(model) -> None:
    try:
        generate_answer(
            "What is the answer?",
            [],
            generate_text=model.generate,
            enabled=True,
            model_name="test-model",
        )
    except ValueError as error:
        assert "passages" in str(error)
    else:
        raise AssertionError("generation accepted an empty evidence set")
    assert model.generate_calls == []
