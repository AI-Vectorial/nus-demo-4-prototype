"""What a refusal says. D5.

Deterministic, and made without a model call (NFR-2): when retrieval is
Insufficient, the user is told the policy set does not cover the question, is
shown every policy area with the team that owns it, and is pointed at
Compliance for anything outside them.

It is deliberately the same message whatever the question was. Routing to the
owner of the nearest document would send "how much parental leave do I get?"
confidently to whichever team's policy happened to score highest.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.ingest.chunk import load_corpus
from app.retrieve.retrieve import Insufficient


@lru_cache(maxsize=4)
def policy_areas(corpus_dir: Path) -> tuple[tuple[str, str], ...]:
    """(title, owner) for every current policy, read from its front matter."""
    return tuple(
        sorted({(d.title, d.owner) for d in load_corpus(corpus_dir) if d.status == "current"})
    )


def refusal_message(result: Insufficient, corpus_dir: Path) -> str:
    if not isinstance(result, Insufficient):
        raise TypeError(f"only an Insufficient retrieval can be refused, not {type(result)}")

    areas = "\n".join(f"- {title} — {owner}" for title, owner in policy_areas(corpus_dir))
    return (
        "Aldermere's policy set does not cover this question, so I have not answered it.\n\n"
        "I can only answer from these policies. If your question belongs to one of them, "
        f"its owning team can help:\n\n{areas}\n\n"
        "For anything else, contact Compliance."
    )
