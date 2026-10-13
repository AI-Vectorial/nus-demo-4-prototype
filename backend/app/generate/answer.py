"""Compose an answer from grounded passages -- or degrade honestly.

compose() accepts only Grounded, so it cannot run on a refusal (REQ-R3). The
model sees the retrieved passages and nothing else (REQ-G1, REQ-G2), under a
prompt kept in a versioned file (REQ-G4). Every Answered records the prompt
version, model and latency that produced it (REQ-G5).

The kill switch (REQ-G6): with GENERATION_ENABLED=false, or when the provider
fails, the result is Degraded -- the same passages, no composed answer, and a
reason. Less useful, still honest, still working.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.generate import ProviderError
from app.retrieve.retrieve import Grounded
from app.retrieve.store import Hit

log = logging.getLogger(__name__)

PROMPT_DIR = Path(__file__).parent / "prompts"
PROMPT_VERSION = "answer_v1"

Generate = Callable[..., str]


@dataclass(frozen=True)
class Answered:
    text: str
    hits: tuple[Hit, ...]
    model: str
    prompt_version: str
    latency_ms: int


@dataclass(frozen=True)
class Degraded:
    hits: tuple[Hit, ...]
    reason: str


@lru_cache(maxsize=1)
def system_prompt() -> str:
    return (PROMPT_DIR / f"{PROMPT_VERSION}.md").read_text(encoding="utf-8").strip()


def _passage(number: int, hit: Hit) -> str:
    version = hit.metadata.get("version", "?")
    status = hit.metadata.get("status", "current")
    label = "current"
    if status == "superseded":
        label = "SUPERSEDED — withdrawn, do not answer from this"
    return (
        f"[{number}] {hit.document_title} v{version} ({label})\n"
        f"Section: {hit.section}\n\n{hit.text}"
    )


def user_prompt(question: str, grounded: Grounded) -> str:
    passages = "\n\n---\n\n".join(_passage(i + 1, hit) for i, hit in enumerate(grounded.hits))
    return f"Policy passages:\n\n{passages}\n\n---\n\nQuestion: {question}"


def compose(
    question: str,
    grounded: Grounded,
    *,
    generate: Generate,
    model_name: str,
    enabled: bool,
) -> Answered | Degraded:
    if not isinstance(grounded, Grounded):
        raise TypeError(f"only a Grounded retrieval can be composed, not {type(grounded)}")
    if not enabled:
        return Degraded(grounded.hits, reason="generation disabled")

    started = time.monotonic()
    try:
        text = generate(user_prompt(question, grounded), system=system_prompt())
    except ProviderError as error:
        log.warning("generation degraded: %s", error)
        return Degraded(grounded.hits, reason="model provider unreachable")

    return Answered(
        text=text,
        hits=grounded.hits,
        model=model_name,
        prompt_version=PROMPT_VERSION,
        latency_ms=int((time.monotonic() - started) * 1000),
    )
