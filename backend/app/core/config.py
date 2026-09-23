"""Runtime configuration, read once at import.

Everything the application needs to reach the outside world arrives as an
environment variable, so a deployment can be repointed without a rebuild.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
    return [o.strip() for o in raw.split(",") if o.strip()]


@dataclass(frozen=True)
class Settings:
    # Identity of the running build, so a failed rollout is distinguishable
    # from a stale one.
    build_sha: str = os.getenv("RAILWAY_GIT_COMMIT_SHA", "local")[:7]
    environment: str = os.getenv("RAILWAY_ENVIRONMENT_NAME", "development")

    allowed_origins: list[str] = field(default_factory=_origins)

    # Postgres holds the corpus metadata and the record of every exchange.
    database_url: str = os.getenv("DATABASE_URL", "")

    # Qdrant holds the embedded passages.
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "policy_passages")

    # Must match the embedding model. Changing it means re-indexing the corpus.
    embedding_dim: int = int(os.getenv("EMBEDDING_DIM", "1024"))

    # Below this, retrieval is treated as having found nothing and the
    # assistant refuses rather than composing an answer from weak matches.
    min_score: float = float(os.getenv("MIN_SCORE", "0.35"))

    @property
    def database_configured(self) -> bool:
        return bool(self.database_url)


settings = Settings()
