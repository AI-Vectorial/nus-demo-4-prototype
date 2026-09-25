"""Composing an answer from retrieved passages -- and what is left when the
model is not there.

Two things are deliberate about this module.

`answer()` takes `Grounded`, never `RetrievalResult`. A refusal cannot reach
the model here because it is the wrong type, which is REQ-R3 enforced by the
type system rather than by a reviewer remembering.

The kill switch (REQ-G6) is written beside the call it replaces, not bolted on
afterwards. A provider failure degrades and returns; it never escapes this
function. Every caller therefore handles degraded mode from the first day,
which is the only time that is cheap to arrange.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files

from app.core.config import settings
from app.generate import ProviderError, generate
from app.retrieve.store import Grounded, Hit

log = logging.getLogger(__name__)

__all__ = ["Answer", "Citation", "answer", "prompt_text"]

# REQ-G4: the prompt is a versioned file, not a string literal. The version
# recorded against every answer (REQ-G5) is the filename, so a change to the
# wording that is not a new file is a change that cannot be told apart later.
PROMPT_FILE = "answer.v1.md"
PROMPT_VERSION = PROMPT_FILE.removesuffix(".md")


@dataclass(frozen=True)
class Citation:
    """One section an answer rests on. The shape PRD section 5 serves."""

    document_id: str
    document_title: str
    section: str
    version: str
    status: str
    score: float


@dataclass(frozen=True)
class Answer:
    """What generation produced, including when it produced nothing."""

    text: str | None  # None when degraded -- never an empty-looking answer
    citations: list[Citation]
    degraded: bool
    prompt_version: str
    model: str
    latency_ms: int
    # The passages were retrieved, but they did not answer the question and the
    # model said so. Not the same as degraded (the model is fine) and not the
    # same as an answer, so the caller renders it as a refusal.
    declined: bool = False


# The prompt asks for this exact prefix when the passages do not answer the
# question. A sentinel rather than phrase-matching the model's prose, because
# prose changes with the model and a missed match renders a refusal as an answer.
DECLINED_MARKER = "CANNOT_ANSWER"


@lru_cache(maxsize=1)
def prompt_text() -> str:
    """The system prompt, read from its versioned file.

    Read through importlib.resources rather than a path assembled from
    __file__, so it resolves the same way from the container's /srv/app as it
    does from a checkout -- and fails at the first call rather than at the
    first deployment.
    """
    return (
        files("app.generate")
        .joinpath("prompts")
        .joinpath(PROMPT_FILE)
        .read_text(encoding="utf-8")
    )


def answer(result: Grounded, history: list[tuple[str, str]] | None = None) -> Answer:
    """Compose an answer from retrieved passages and nothing else.

    `history` is the recent (role, content) turns of the conversation, oldest
    first, so a follow-up resolves what "it" refers to (REQ-C3). It is context
    for reading the question -- retrieval has already run again on this turn
    (REQ-C5), so the passages below are this question's, not the last one's.

    Returns a degraded Answer when generation is switched off or the provider
    is unreachable (REQ-G6). It does not raise for either: a policy search
    with no composed answer is still a working product, and a 500 is not.
    """
    started = time.perf_counter()
    citations = _citations(result.passages)

    if not settings.generation_enabled:
        return _degraded(citations, started, "GENERATION_ENABLED is false")

    try:
        text = generate(_compose(result, history or []), system=prompt_text())
    except ProviderError as error:
        # Reported, not handled: the product carries on with the passages.
        log.warning("degrading -- the model is unreachable: %s", error)
        return _degraded(citations, started, "provider unreachable")

    if not text.strip():
        # An empty string renders as an answer that says nothing, which reads
        # as an answer. Degraded at least reads as degraded.
        return _degraded(citations, started, "the model returned nothing")

    # Retrieval cleared the threshold, but the passages did not actually answer
    # the question and the model said so. Rendered as an answer this is
    # contradictory -- "the policy set does not cover that" sitting above a list
    # of SOURCES reads as though the sources were used. It is a refusal.
    stripped = text.strip()
    if stripped.upper().startswith(DECLINED_MARKER):
        reason = stripped[len(DECLINED_MARKER) :].lstrip(": ").strip()
        log.info("model declined: %s", reason or "no reason given")
        return Answer(
            text=reason or "The passages found do not answer this question.",
            citations=[],
            degraded=False,
            declined=True,
            prompt_version=PROMPT_VERSION,
            model=settings.llm_model,
            latency_ms=_elapsed(started),
        )

    return Answer(
        text=stripped,
        citations=citations,
        degraded=False,
        prompt_version=PROMPT_VERSION,
        model=settings.llm_model,
        latency_ms=_elapsed(started),
    )


def _degraded(citations: list[Citation], started: float, why: str) -> Answer:
    """The passages, honestly labelled as not an answer."""
    log.info("degraded answer: %s", why)
    return Answer(
        text=None,
        citations=citations,
        degraded=True,
        prompt_version=PROMPT_VERSION,
        model=settings.llm_model,
        latency_ms=_elapsed(started),
    )


def _elapsed(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def _citations(passages: list[Hit]) -> list[Citation]:
    """One citation per section, best score wins (D7).

    Two passages from 4.2 are one citation. Grouping by document instead would
    lose the section, and the section is the part a human can go and check.
    """
    best: dict[tuple[str, str], Citation] = {}
    for hit in passages:
        key = (hit.document_id, hit.section)
        current = best.get(key)
        if current is not None and current.score >= hit.score:
            continue
        best[key] = Citation(
            document_id=hit.document_id,
            document_title=hit.document_title,
            section=hit.section,
            version=str(hit.metadata.get("version", "")),
            status=_status(hit),
            score=hit.score,
        )
    return sorted(best.values(), key=lambda citation: citation.score, reverse=True)


def _status(hit: Hit) -> str:
    return str(hit.metadata.get("status", "current")) or "current"


def _compose(result: Grounded, history: list[tuple[str, str]]) -> str:
    """The user half of the prompt: prior turns, the passages, the question.

    The question goes last because it is what must be answered, and a model
    reading a long prompt weights the end of it most.
    """
    parts: list[str] = []

    recent = _recent(history)
    if recent:
        parts.append(
            "Earlier in this conversation (context for reading the question -- "
            f"do not answer these again):\n{recent}"
        )

    parts.append(f"Policy passages:\n\n{_passages(result.passages)}")
    parts.append(
        "Question:\n"
        f"{_question(result, history)}\n\n"
        "Answer from the passages above and nothing else."
    )
    return "\n\n".join(parts)


def _recent(history: list[tuple[str, str]]) -> str:
    """The last CONTEXT_MESSAGES turns (D8), oldest first.

    Trimmed here as well as by the caller, so the limit holds wherever the
    history came from. Too many turns drag an answer toward an earlier topic.
    """
    turns = [
        f"{'User' if role == 'user' else 'Assistant'}: {content.strip()}"
        for role, content in history[-settings.context_messages :]
        if content and content.strip()
    ]
    return "\n".join(turns)


def _passages(passages: list[Hit]) -> str:
    """The passages, each labelled with the section a human would check.

    A superseded passage is labelled loudly rather than dropped (D4, REQ-I7):
    the prompt is told to prefer the current one and say what changed, which
    it cannot do if the old version never arrives.
    """
    blocks = []
    for index, hit in enumerate(passages, start=1):
        status = _status(hit)
        label = f"[{index}] {hit.document_title} -- {hit.section}"
        version = str(hit.metadata.get("version", "")).strip()
        if version:
            label += f" (version {version})"
        if status != "current":
            label += f"  *** {status.upper()} ***"
        blocks.append(f"{label}\n{hit.text.strip()}")
    return "\n\n".join(blocks)


def _question(result: Grounded, history: list[tuple[str, str]]) -> str:
    """What was asked. Falls back to the last user turn if a caller built a
    Grounded without one, so an answer is never composed with no question."""
    if result.question.strip():
        return result.question.strip()
    for role, content in reversed(history):
        if role == "user" and content.strip():
            return content.strip()
    return ""
