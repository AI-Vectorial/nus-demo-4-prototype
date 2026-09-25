"""The retrieval interface.

Deliberately expressed in terms of policy passages rather than the storage
engine underneath: nothing in this module names a vendor, a collection, a point
or a row. A caller asks for the passages nearest a query embedding and gets
domain objects back.

That constraint is the whole point. It keeps retrieval swappable, and -- more
usefully day to day -- it keeps the ingest, generate and feature code free of
storage detail, so a table writing a feature never has to learn the client
library to use what it returns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class Passage:
    """One chunk of one policy document, ready to be stored."""

    id: str
    text: str
    document_id: str
    document_title: str
    section: str
    embedding: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Hit:
    """One retrieved passage and how well it matched."""

    passage_id: str
    text: str
    document_id: str
    document_title: str
    section: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Grounded:
    """Retrieval found passages the corpus can answer from.

    Carries the question it was asked, so generation never has to be told
    twice -- and so a Grounded result is a complete record of the search that
    produced it.
    """

    passages: list[Hit]
    question: str = ""


@dataclass(frozen=True)
class Insufficient:
    """Retrieval found nothing good enough. Generation must not run.

    `best_score` is the highest score seen *before* the threshold dropped it,
    which is what makes a refusal evidence rather than a shrug: it is the
    number MIN_SCORE was tuned against. `owner_hint` names the team that owns
    the document it nearly matched, so the refusal can send someone somewhere.
    """

    reason: str
    best_score: float
    owner_hint: str | None = None


# REQ-R3. Two outcomes, two types -- never an ambiguous empty list. Generation
# accepts Grounded only, so a refusal cannot reach the model by accident: the
# type checker refuses it before a reviewer has to notice.
RetrievalResult = Grounded | Insufficient


@runtime_checkable
class VectorStore(Protocol):
    """What the application needs from a vector store. Nothing more."""

    def ensure_ready(self) -> None:
        """Create whatever the store needs, if it is not already there.

        Must be safe to call repeatedly -- it runs on every boot.
        """

    def recreate(self) -> None:
        """Throw away everything stored and start empty.

        What `python -m app.ingest --force` is (REQ-I5). Kept on the interface
        rather than reached for through the client, so re-indexing does not
        require knowing which engine is underneath.
        """

    def upsert(self, passages: list[Passage]) -> int:
        """Store passages, replacing any with the same id. Returns the count."""

    def search(self, embedding: list[float], limit: int = 5, min_score: float = 0.0) -> list[Hit]:
        """Return the closest passages, best first, dropping weak matches.

        Returning an empty list is a valid and expected answer: it is what
        makes the assistant refuse instead of inventing something.
        """

    def count(self) -> int:
        """How many passages are indexed."""

    def health(self) -> tuple[bool, str]:
        """(reachable, detail) -- for /healthz. Must never raise."""
