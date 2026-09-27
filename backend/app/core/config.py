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
    # DATABASE_NAME is set per table and swapped into the URL, so each table
    # writes to its own database on the shared instance.
    database_url: str = os.getenv("DATABASE_URL", "")
    database_name: str = os.getenv("DATABASE_NAME", "")

    # Which table this deployment belongs to. Display only.
    table_id: str = os.getenv("TABLE_ID", "")

    # Qdrant holds the embedded passages.
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "policy_passages")

    # Must match the embedding model. Changing it means re-indexing the corpus.
    embedding_dimensions: int = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))

    # --- OpenRouter: the only model credential -----------------------------
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_base_url: str = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    )

    llm_model: str = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    llm_timeout_seconds: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
    llm_max_retries: int = int(os.getenv("LLM_MAX_RETRIES", "3"))

    # Your decision -- PRD section 9, D0. The Qdrant collection is created at
    # whatever dimension you index with, so these two must agree.
    embedding_model_slug: str = os.getenv(
        "EMBEDDING_MODEL_SLUG", "openai/text-embedding-3-small"
    )
    embedding_batch_size: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "96"))

    # Turning generation off must leave a working policy search behind.
    generation_enabled: bool = os.getenv("GENERATION_ENABLED", "true").lower() != "false"

    # How many recent turns a follow-up question is answered with. Yours -- D8.
    # Retrieval still runs on every turn: context informs the answer, it never
    # replaces the search.
    context_messages: int = int(os.getenv("CONTEXT_MESSAGES", "5"))

    # The team's PRD section 10 decisions. Captured raw and parsed on use, with
    # no default: an unset value fails the request that needs it, loudly, rather
    # than the app picking a number nobody defended. The app still loads, so
    # /healthz answers -- NFR-5. The values and the reasons: docs/design/decisions.md
    _min_score: str | None = field(default_factory=lambda: os.getenv("MIN_SCORE"))
    _chunk_max_tokens: str | None = field(default_factory=lambda: os.getenv("CHUNK_MAX_TOKENS"))
    _chunk_overlap_tokens: str | None = field(
        default_factory=lambda: os.getenv("CHUNK_OVERLAP_TOKENS")
    )
    _retrieve_top_k: str | None = field(default_factory=lambda: os.getenv("RETRIEVE_TOP_K"))

    @property
    def database_configured(self) -> bool:
        return bool(self.database_url)

    # Below this, retrieval is treated as having found nothing and the
    # assistant refuses rather than composing an answer from weak matches. D2.
    @property
    def min_score(self) -> float:
        return float(_required("MIN_SCORE", self._min_score))

    # A section longer than this splits, on paragraph boundaries. D1.
    @property
    def chunk_max_tokens(self) -> int:
        return int(_required("CHUNK_MAX_TOKENS", self._chunk_max_tokens))

    # How much of a split section's end the next piece repeats. D1.
    @property
    def chunk_overlap_tokens(self) -> int:
        return int(_required("CHUNK_OVERLAP_TOKENS", self._chunk_overlap_tokens))

    # How many passages a question retrieves before the threshold is applied. D3.
    @property
    def retrieve_top_k(self) -> int:
        return int(_required("RETRIEVE_TOP_K", self._retrieve_top_k))


class ConfigurationError(RuntimeError):
    """A value the team must choose has not been set in the environment."""


def _required(name: str, raw: str | None) -> str:
    if raw is None or not raw.strip():
        raise ConfigurationError(
            f"{name} is not set. It is a team decision with no default -- "
            "see docs/design/decisions.md."
        )
    return raw


settings = Settings()
