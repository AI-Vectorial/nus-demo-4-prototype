"""Runtime configuration, read once at import.

Everything the application needs to reach the outside world arrives as an
environment variable, so a deployment can be repointed without a rebuild.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# backend/, so the corpus resolves the same from a checkout and from the image.
_BACKEND = Path(__file__).resolve().parents[2]


def _origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
    return [o.strip() for o in raw.split(",") if o.strip()]


def _optional(name: str, cast):
    """A team decision has no fallback in code: unset stays None until used."""
    raw = os.getenv(name, "").strip()
    return cast(raw) if raw else None


class MissingSetting(RuntimeError):
    """A decision the team has to make was not supplied by the environment."""


def require(value, name: str):
    """The value, or a message that names the setting that is missing."""
    if value is None:
        raise MissingSetting(f"{name} is not set. It is a team decision -- see docs/design/.")
    return value


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

    # How many recent messages (rows, not turns) a follow-up sees -- D8. The
    # same window supplies the user questions retrieval runs on -- D9.
    context_messages: int = int(os.getenv("CONTEXT_MESSAGES", "5"))

    # Below this a passage is discarded, and with none left the assistant
    # refuses -- D2. No fallback: the value is measured, then signed off.
    min_score: float | None = _optional("MIN_SCORE", float)

    # One passage per section, the ceiling only a guard -- D1.
    chunk_max_tokens: int | None = _optional("CHUNK_MAX_TOKENS", int)
    chunk_overlap_tokens: int | None = _optional("CHUNK_OVERLAP_TOKENS", int)

    # A ceiling on passages fetched before the threshold -- D3.
    retrieve_top_k: int | None = _optional("RETRIEVE_TOP_K", int)

    corpus_dir: Path = Path(os.getenv("CORPUS_DIR", str(_BACKEND / "corpus")))

    # Versioned prompt and refusal text (REQ-G4), outside the code.
    prompts_dir: Path = Path(os.getenv("PROMPTS_DIR", str(_BACKEND / "prompts")))

    @property
    def database_configured(self) -> bool:
        return bool(self.database_url)


settings = Settings()
