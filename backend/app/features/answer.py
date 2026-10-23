from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.generate import ProviderError, generate
from app.retrieve.store import Hit

_PROMPT_PATH = Path(__file__).resolve().parents[1] / "generate" / "prompts" / "v2.md"


@dataclass(frozen=True)
class Answered:
    answer: str
    citations: list[Hit]
    model: str
    prompt_version: str
    latency_ms: int


@dataclass(frozen=True)
class Degraded:
    answer: None
    citations: list[Hit]
    model: str
    prompt_version: str
    latency_ms: int


type GenerationResult = Answered | Degraded


def _passage_context(hits: list[Hit]) -> str:
    return "\n\n".join(
        f"[{hit.document_title} — {hit.section}, version {hit.metadata.get('version', '')}, "
        f"status {hit.metadata.get('status', '')}]\n{hit.text}"
        for hit in hits
    )


def generate_answer(
    question: str,
    hits: list[Hit],
    *,
    conversation_context: str = "",
    generate_text=generate,
    enabled: bool | None = None,
    model_name: str | None = None,
) -> GenerationResult:
    if not hits:
        raise ValueError("retrieved passages are required for generation")

    is_enabled = settings.generation_enabled if enabled is None else enabled
    selected_model = settings.llm_model if model_name is None else model_name
    prompt_version = _PROMPT_PATH.stem
    prompt_template = _PROMPT_PATH.read_text(encoding="utf-8")
    prompt = prompt_template.replace("{question}", question).replace(
        "{passages}", _passage_context(hits)
    ).replace("{conversation_context}", conversation_context)

    if not is_enabled:
        return Degraded(
            answer=None,
            citations=hits,
            model=selected_model,
            prompt_version=prompt_version,
            latency_ms=0,
        )

    started = time.perf_counter()
    try:
        answer = generate_text(
            prompt,
            system=(
                "Use only the policy passages in the request. Never decide "
                "which policy controls when passages conflict."
            ),
        )
    except ProviderError:
        return Degraded(
            answer=None,
            citations=hits,
            model=selected_model,
            prompt_version=prompt_version,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
    return Answered(
        answer=answer,
        citations=hits,
        model=selected_model,
        prompt_version=prompt_version,
        latency_ms=int((time.perf_counter() - started) * 1000),
    )
