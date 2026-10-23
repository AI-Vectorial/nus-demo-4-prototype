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

    # The fallback matters as much as the variable. A Codespace sets no
    # LLM_MODEL at all -- docker-compose does not declare one and .env does not
    # carry one -- so whatever stands here is the model the product runs
    # locally while a table builds, and it has to be one the OpenRouter
    # workspace actually allows. gpt-oss-120b is blocked by the guardrail.
    llm_model: str = os.getenv("LLM_MODEL", "anthropic/claude-haiku-5.5")
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

    # How many passages retrieval returns before the threshold is applied. D3.
    retrieve_top_k: int = int(os.getenv("RETRIEVE_TOP_K", "5"))

    # Below this, retrieval is treated as having found nothing and the
    # assistant refuses rather than composing an answer from weak matches.
    # Yours to choose -- D2. Tune it against corpus/EVALUATION.md.
    # No default. The value is the team's decision (D2), set in the environment
    # once measured against corpus/EVALUATION.md. None means retrieval refuses to run.
    min_score: float | None = float(os.environ["MIN_SCORE"]) if os.getenv("MIN_SCORE") else None

    @property
    def database_configured(self) -> bool:
        return bool(self.database_url)


settings = Settings()
