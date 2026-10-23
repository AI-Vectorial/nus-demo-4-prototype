"""Compose an answer from retrieved passages, or degrade to the passages alone.

Callers pass a Grounded result from retrieval, so a refusal can never reach this
module. The model is reached only through the generate function passed in, which
in production is app.generate.generate. The kill switch (REQ-G6) is here, not at
the callers: with generation off, or the provider down, the caller gets the
passages with no answer and a reason.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.generate.client import ProviderError
from app.retrieve.search import Grounded
from app.retrieve.store import Hit

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
PROMPT_VERSION = "answer_v1"
PROMPT_PATH = PROMPTS_DIR / f"{PROMPT_VERSION}.md"

SUPERSEDED_NOTICE = (
    "Retrieval also found a superseded policy version. Check the status of each cited "
    "section before acting on this answer."
)


@dataclass(frozen=True)
class Answered:
    text: str
    hits: list[Hit]
    prompt_version: str
    model: str
    latency_ms: int
    notice: str | None


@dataclass(frozen=True)
class Degraded:
    hits: list[Hit]
    reason: str


Composition = Answered | Degraded


def _passage_block(hit: Hit) -> str:
    version = hit.metadata.get("version", "")
    status = hit.metadata.get("status", "")
    return (
        f"[{hit.document_title}, version {version}, {hit.section}, status: {status}]\n"
        f"{hit.text}"
    )


def build_prompt(question: str, hits: list[Hit]) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    passages = "\n\n".join(_passage_block(hit) for hit in hits)
    return template.replace("{question}", question).replace("{passages}", passages)


def compose(
    question: str,
    grounded: Grounded,
    generate: Callable[..., str],
    *,
    enabled: bool | None = None,
) -> Composition:
    """An answer from the passages, or the passages with a reason. REQ-G1 .. G6."""
    on = settings.generation_enabled if enabled is None else enabled
    if not on:
        return Degraded(hits=grounded.hits, reason="generation is switched off")

    started = time.perf_counter()
    try:
        text = generate(build_prompt(question, grounded.hits), system=None, temperature=0.0)
    except ProviderError as error:
        return Degraded(hits=grounded.hits, reason=str(error))
    latency_ms = int((time.perf_counter() - started) * 1000)

    superseded = any(h.metadata.get("status") == "superseded" for h in grounded.hits)
    return Answered(
        text=text,
        hits=grounded.hits,
        prompt_version=PROMPT_VERSION,
        model=settings.llm_model,
        latency_ms=latency_ms,
        notice=SUPERSEDED_NOTICE if superseded else None,
    )
