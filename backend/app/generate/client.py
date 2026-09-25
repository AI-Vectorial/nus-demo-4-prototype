"""The OpenRouter client.

The ONLY module in the application permitted to import a model provider SDK.
Everything else goes through generate() and embed() in app.generate, so the
provider can change without touching a single caller -- which is what makes the
brief's kill switch possible at all.

A test asserts this boundary and fails the build if a second module imports the
SDK.  See tests/regression/test_provider_boundary.py.
"""

from __future__ import annotations

import logging
import time

from openai import APIError, APITimeoutError, OpenAI, RateLimitError

from app.core.config import settings

log = logging.getLogger(__name__)


class ProviderError(RuntimeError):
    """A model call failed.

    Raised instead of the SDK's own exceptions so that callers can handle a
    provider failure without importing the SDK to catch it -- which would
    breach the boundary this module exists to hold.
    """

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


def _client() -> OpenAI:
    if not settings.openrouter_api_key:
        raise ProviderError(
            "OPENROUTER_API_KEY is not set. In a Codespace it should already be "
            "in your environment; if it is not, tell an instructor rather than "
            "pasting a key into a file."
        )
    return OpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        timeout=settings.llm_timeout_seconds,
        max_retries=0,  # retries are handled here, so backoff is visible
    )


def _call(operation, *, what: str, attempts: int):
    """Run a provider call with backoff, converting SDK errors to ProviderError."""
    last: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except RateLimitError as error:
            last = error
            wait = attempt * 5
            log.warning("%s rate limited, waiting %ss (attempt %d)", what, wait, attempt)
            time.sleep(wait)
        except APITimeoutError as error:
            last = error
            log.warning("%s timed out (attempt %d)", what, attempt)
        except APIError as error:
            # 4xx other than rate limiting will not succeed on a retry.
            if getattr(error, "status_code", 500) < 500:
                raise ProviderError(f"{what} failed: {error}") from error
            last = error
            log.warning("%s provider error (attempt %d)", what, attempt)
        time.sleep(1)

    raise ProviderError(
        f"{what} failed after {attempts} attempts: {last}", retryable=True
    ) from last


def generate(prompt: str, *, system: str | None = None, temperature: float = 0.0) -> str:
    """Ask the model to write something. Returns the text it wrote."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = _call(
        lambda: _client().chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=temperature,
        ),
        what="generate",
        attempts=settings.llm_max_retries,
    )
    return (response.choices[0].message.content or "").strip()


def embed(texts: list[str]) -> list[list[float]]:
    """Turn texts into vectors, in the order given.

    Batched: a corpus larger than EMBEDDING_BATCH_SIZE becomes several requests
    rather than one that fails.
    """
    if not texts:
        return []

    size = settings.embedding_batch_size
    vectors: list[list[float]] = []

    for start in range(0, len(texts), size):
        batch = texts[start : start + size]
        response = _call(
            lambda b=batch: _client().embeddings.create(
                model=settings.embedding_model_slug,
                input=b,
            ),
            what="embed",
            attempts=settings.llm_max_retries,
        )
        vectors.extend(item.embedding for item in response.data)

    if vectors and len(vectors[0]) != settings.embedding_dimensions:
        raise ProviderError(
            f"{settings.embedding_model_slug} returned {len(vectors[0])} dimensions "
            f"but EMBEDDING_DIMENSIONS is {settings.embedding_dimensions}. "
            "A Qdrant collection is fixed at the dimension it was created with, so "
            "these must agree. Fix the setting, then re-index with --force."
        )
    return vectors


def health() -> tuple[bool, str]:
    """Never raises: /healthz must answer even when the provider is down."""
    if not settings.openrouter_api_key:
        return False, "OPENROUTER_API_KEY not set"
    return True, f"{settings.llm_model} configured"
