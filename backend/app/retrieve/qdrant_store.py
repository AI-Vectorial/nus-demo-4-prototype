"""Qdrant-backed retrieval.

The only module in the application that imports the Qdrant client. Everything
else works through the VectorStore interface in app.retrieve.store, so client
types never escape this file.
"""

from __future__ import annotations

import logging

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings
from app.retrieve.store import Hit, Passage

log = logging.getLogger(__name__)


class QdrantVectorStore:
    """Policy passages in a Qdrant collection, one point per passage."""

    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        collection: str | None = None,
        dim: int | None = None,
    ) -> None:
        self.collection = collection or settings.qdrant_collection
        self.dim = dim or settings.embedding_dimensions
        self._client = QdrantClient(
            url=url or settings.qdrant_url,
            api_key=api_key or settings.qdrant_api_key or None,
            timeout=10,
        )

    def ensure_ready(self) -> None:
        if self._client.collection_exists(self.collection):
            return
        self._client.create_collection(
            collection_name=self.collection,
            # Cosine because the embeddings are normalised; scores land in
            # [-1, 1] and MIN_SCORE is expressed on that scale.
            vectors_config=VectorParams(size=self.dim, distance=Distance.COSINE),
        )
        log.info("created Qdrant collection %s (dim=%d)", self.collection, self.dim)

    def recreate(self) -> None:
        """Drop the collection and build it again, empty (REQ-I5).

        Deleting rather than emptying, because the dimension is fixed at
        creation: changing EMBEDDING_DIMENSIONS is exactly when --force is run.
        """
        if self._client.collection_exists(self.collection):
            self._client.delete_collection(self.collection)
            log.info("deleted Qdrant collection %s", self.collection)
        self.ensure_ready()

    def upsert(self, passages: list[Passage]) -> int:
        if not passages:
            return 0
        self._client.upsert(
            collection_name=self.collection,
            points=[
                PointStruct(
                    id=p.id,
                    vector=p.embedding,
                    payload={
                        "text": p.text,
                        "document_id": p.document_id,
                        "document_title": p.document_title,
                        "section": p.section,
                        **p.metadata,
                    },
                )
                for p in passages
            ],
        )
        return len(passages)

    def search(self, embedding: list[float], limit: int = 5, min_score: float = 0.0) -> list[Hit]:
        results = self._client.query_points(
            collection_name=self.collection,
            query=embedding,
            limit=limit,
            score_threshold=min_score or None,
            with_payload=True,
        ).points

        hits: list[Hit] = []
        for r in results:
            payload = dict(r.payload or {})
            hits.append(
                Hit(
                    passage_id=str(r.id),
                    text=payload.pop("text", ""),
                    document_id=payload.pop("document_id", ""),
                    document_title=payload.pop("document_title", ""),
                    section=payload.pop("section", ""),
                    score=float(r.score),
                    metadata=payload,
                )
            )
        return hits

    def count(self) -> int:
        if not self._client.collection_exists(self.collection):
            return 0
        return int(self._client.count(self.collection, exact=True).count)

    def health(self) -> tuple[bool, str]:
        """Never raises: /healthz must answer even when Qdrant is down."""
        try:
            if not self._client.collection_exists(self.collection):
                return True, "reachable, collection not created yet"
            return True, f"{self.count()} passages indexed"
        except Exception as exc:  # noqa: BLE001 - reported, not handled
            return False, f"unreachable: {type(exc).__name__}"
