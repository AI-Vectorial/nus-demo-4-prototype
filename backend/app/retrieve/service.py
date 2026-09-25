"""Retrieve, or refuse -- and they are different types on purpose.

REQ-R3. A question either produces passages the corpus supports (`Grounded`)
or an explicit statement that it does not (`Insufficient`). Nothing here ever
returns a bare list, because a bare empty list is the shape that lets someone
call the model with no context and get a confident invention back.

The threshold is applied here rather than in the prompt, because a refusal must
make no model call at all (NFR-2). A model asked whether it knows something
answers with whatever it has; the rule has to live in code.
"""

from __future__ import annotations

import logging

from app.core.config import settings
from app.generate import embed
from app.retrieve import get_vector_store
from app.retrieve.store import Grounded, Hit, Insufficient, RetrievalResult

log = logging.getLogger(__name__)

__all__ = ["Grounded", "Insufficient", "RetrievalResult", "retrieve"]

# Where to send someone when nothing in the corpus is even close. Every
# document names an owning team, so a near miss can do better than this.
FALLBACK_OWNER = "the Policy Office"


def retrieve(question: str) -> RetrievalResult:
    """Find the passages that answer a question, or say why none do.

    Searches unfiltered and applies MIN_SCORE (REQ-R2, REQ-R4) here, so a
    refusal can report the score it rejected -- the evidence behind D2 -- and
    name the team that owns the document it came closest to (D5).

    A provider failure while embedding is not caught: retrieval genuinely did
    not happen, and reporting that as "the corpus does not cover this" would
    be a lie the user cannot tell from the truth.
    """
    asked = question.strip()
    if not asked:
        return Insufficient(
            reason="No question was asked.", best_score=0.0, owner_hint=None
        )

    embedding = embed([asked])[0]
    # min_score=0.0 deliberately: the near miss is what a refusal is made of.
    hits = get_vector_store().search(
        embedding, limit=settings.retrieve_top_k, min_score=0.0
    )

    grounded = [hit for hit in hits if hit.score >= settings.min_score]
    if grounded:
        return Grounded(passages=grounded, question=asked)

    near_miss = max(hits, key=lambda hit: hit.score, default=None)
    best_score = near_miss.score if near_miss else 0.0
    log.info(
        "refusing: best score %.3f is below MIN_SCORE %.3f",
        best_score,
        settings.min_score,
    )
    return Insufficient(
        reason=_reason(near_miss),
        best_score=best_score,
        owner_hint=_owner(near_miss),
    )


def _owner(near_miss: Hit | None) -> str | None:
    """The team that owns the nearest document, if ingestion recorded one."""
    if near_miss is None:
        return None
    owner = str(near_miss.metadata.get("owner", "")).strip()
    return owner or None


def _reason(near_miss: Hit | None) -> str:
    """What the refusal says. D5: what is not covered, and who to ask instead.

    "I don't know" leaves someone exactly where they started, so the reason
    names the closest policy -- which is how they can tell a gap in the corpus
    from a badly worded question -- and then names a real team.
    """
    if near_miss is None:
        return (
            "The policy corpus does not cover this, and nothing in it came close. "
            f"Ask {FALLBACK_OWNER}, who can say whether a policy exists."
        )

    owner = _owner(near_miss) or FALLBACK_OWNER
    return (
        "The policy corpus does not cover this. The closest match was "
        f"{near_miss.document_title} ({near_miss.section}), which does not "
        f"answer it. {owner} owns that policy and can say where this sits."
    )
