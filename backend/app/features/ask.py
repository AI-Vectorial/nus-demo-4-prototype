"""A question to an outcome: retrieve, then refuse, compose, or degrade.

The order is the rule. Retrieval decides whether there is anything to answer
from (REQ-R3), and only then is the model asked to write (REQ-G1). When the
model is switched off or unreachable, what was retrieved is returned without
a composed answer (REQ-G6) -- still a working policy search.

No database here: the record of the exchange is written by the API.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from app.core.config import settings
from app.generate import ProviderError
from app.generate.prompt import load_prompt, refusal_text
from app.retrieve import Grounded, Hit, VectorStore, retrieve
from app.retrieve.retrieve import Embed

log = logging.getLogger(__name__)

Generate = Callable[..., str]


@dataclass(frozen=True)
class Answered:
    text: str
    citations: list[Hit]
    model: str
    prompt_version: str


@dataclass(frozen=True)
class Refused:
    text: str


@dataclass(frozen=True)
class Degraded:
    citations: list[Hit]


Outcome = Answered | Refused | Degraded


def _cited(hits: list[Hit]) -> list[Hit]:
    """D7: one citation per passage, the same section and version only once."""
    seen: set[tuple[str, str, str]] = set()
    cited: list[Hit] = []
    for hit in hits:
        key = (hit.document_id, hit.section, str(hit.metadata.get("version")))
        if key not in seen:
            seen.add(key)
            cited.append(hit)
    return cited


def answer_question(
    question: str,
    store: VectorStore,
    embed: Embed,
    generate: Generate,
    *,
    generation_enabled: bool | None = None,
    min_score: float | None = None,
) -> Outcome:
    retrieval = retrieve(question, store, embed, min_score=min_score)
    if not isinstance(retrieval, Grounded):
        return Refused(text=refusal_text())

    citations = _cited(retrieval.hits)
    enabled = settings.generation_enabled if generation_enabled is None else generation_enabled
    if not enabled:
        return Degraded(citations=citations)

    prompt = load_prompt()
    try:
        text = generate(prompt.render(question, citations), system=prompt.system)
    except ProviderError as error:
        log.warning("generation unavailable, degrading: %s", error)
        return Degraded(citations=citations)

    return Answered(text=text, citations=citations, model=settings.llm_model,
                    prompt_version=prompt.version)
