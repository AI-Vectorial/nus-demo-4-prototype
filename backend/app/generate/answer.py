"""Composing an answer from grounded passages (F4).

Takes Grounded and nothing else: a refusal never reaches this module. With
GENERATION_ENABLED=false, or when the provider fails, the result is Degraded --
the passages stand on their own, with no composed answer (REQ-G6).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from app.core.config import settings
from app.features.context import Turn
from app.generate import ProviderError
from app.retrieve.retrieve import Grounded

log = logging.getLogger(__name__)

PROMPT_VERSION = "answer-v1"


@dataclass(frozen=True)
class Answered:
    text: str
    prompt_version: str
    model: str


@dataclass(frozen=True)
class Degraded:
    reason: str


def _passage(number: int, hit) -> str:
    version = hit.metadata.get("version", "")
    status = hit.metadata.get("status", "")
    label = "SUPERSEDED" if status == "superseded" else status
    return f"[{number}] {hit.document_title} (v{version}, {label}) — {hit.section}\n{hit.text}"


def render(question: str, history: list[Turn], grounded: Grounded) -> tuple[str, str]:
    """(system, prompt) from the versioned prompt file (REQ-G4)."""
    raw = (settings.prompts_dir / f"{PROMPT_VERSION}.md").read_text(encoding="utf-8")
    system, _, template = raw.partition("\n===\n")
    conversation = "\n".join(f"{t.role.capitalize()}: {t.content}" for t in history) or "(none)"
    passages = "\n\n".join(_passage(i, h) for i, h in enumerate(grounded.hits, start=1))
    prompt = (template.replace("{history}", conversation)
                      .replace("{passages}", passages)
                      .replace("{question}", question))
    return system.strip(), prompt.strip()


def compose(question: str, history: list[Turn], grounded: Grounded,
            generate: Callable[..., str], *, enabled: bool, model_name: str) -> Answered | Degraded:
    if not isinstance(grounded, Grounded):
        raise TypeError("compose() needs Grounded passages; a refusal never reaches the model")
    if not enabled:
        return Degraded("generation is switched off")

    system, prompt = render(question, history, grounded)
    try:
        text = generate(prompt, system=system)
    except ProviderError as error:
        # Handled: the caller shows the passages without an answer (REQ-G6).
        log.warning("generation unavailable, degrading: %s", type(error).__name__)
        return Degraded("the model is unreachable")
    return Answered(text=text, prompt_version=PROMPT_VERSION, model=model_name)
