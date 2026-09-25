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


def _contextualise(question: str, history: list[tuple[str, str]] | None) -> str:
    """The text to embed: the conversation, not just the latest fragment.

    Only the USER turns are carried. Including the assistant's answers drags
    the query toward whatever it happened to say, which is a summary of the
    passages already found -- so retrieval would keep re-finding them and a
    follow-up could never reach a section the first answer missed.

    Trimmed to settings.context_messages (D8), oldest first, so a long
    conversation does not slowly pull every query back toward its opening
    question.
    """
    if not history:
        return question

    asked = [text for role, text in history if role == "user" and text.strip()]
    # The current question may already be the last entry, depending on the
    # caller; do not embed it twice.
    if asked and asked[-1].strip() == question.strip():
        asked = asked[:-1]
    if not asked:
        return question

    recent = asked[-settings.context_messages :]
    return chr(10).join([*recent, question])


def _prefer_current(hits: list[Hit], limit: int) -> list[Hit]:
    """Fill the result with current policy first, then superseded.

    The corpus holds v3.0 and v3.1 of the travel policy, and their passages say
    almost the same thing -- so they score almost the same and compete for the
    same slots. Ranked purely by score, the withdrawn version can crowd the
    current one out of the top k entirely.

    That is not a ranking curiosity. Asked for the evening-meal cap, retrieval
    returned only the superseded section and the answer was that the policy set
    does not give one -- when the current policy gives 40 pounds. A wrong answer,
    which is worse than a refusal and exactly what this product exists not to do.

    Superseded passages are still returned (D4 shows them, flagged) -- they just
    no longer displace current ones. Scores are untouched, so the threshold and
    the refusal evidence still mean what they meant.
    """
    current = [hit for hit in hits if hit.metadata.get("status") != "superseded"]
    superseded = [hit for hit in hits if hit.metadata.get("status") == "superseded"]

    # Keep at least one slot for a superseded passage when there is one, so
    # "has this changed?" is still answerable.
    room = max(limit - 1, 1) if superseded else limit
    chosen = current[:room]
    chosen += superseded[: limit - len(chosen)]
    return sorted(chosen, key=lambda hit: hit.score, reverse=True)


def retrieve(question: str, history: list[tuple[str, str]] | None = None) -> RetrievalResult:
    """Find the passages that answer a question, or say why none do.

    `history` is the recent turns, oldest first. A follow-up is embedded WITH
    the questions that came before it, because on its own it usually carries no
    policy vocabulary at all -- "and what about above 500 pounds?" embeds to
    nothing near the corpus and is refused, even though the answer is one row
    further down the table the previous question already found.

    Retrieval still runs on every turn (REQ-C5). What changes is the text it
    runs ON: the conversation, not the fragment. The answer is still composed
    for the question actually asked.

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

    # Embed the conversation, not just the latest fragment. Grounded still
    # carries the question actually asked, so the answer is composed for it.
    embedding = embed([_contextualise(asked, history)])[0]
    # min_score=0.0 deliberately: the near miss is what a refusal is made of.
    # Over-fetch, because the corpus holds two versions of one policy and their
    # passages are near-duplicates -- see _prefer_current.
    hits = get_vector_store().search(
        embedding, limit=settings.retrieve_top_k * 3, min_score=0.0
    )
    hits = _prefer_current(hits, settings.retrieve_top_k)

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
