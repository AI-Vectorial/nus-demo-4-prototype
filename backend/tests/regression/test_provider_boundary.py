"""The provider boundary.

Model calls go through app.generate, and exactly one module knows which
provider is behind them. These tests keep it that way, because a boundary that
exists only in a docstring stops being true the first time someone is in a
hurry.

The same shape as test_retrieval_contract.py, for the same reason.
"""

from __future__ import annotations

import ast
from pathlib import Path

from app.generate import ProviderError, embed, generate, health

APP = Path(__file__).resolve().parents[2] / "app"

# The one module allowed to import the provider SDK.
CLIENT = "generate/client.py"

# SDKs that would breach the boundary if imported anywhere else.
PROVIDER_SDKS = ("openai", "anthropic", "cohere", "litellm", "httpx")


def _imported_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_only_the_client_imports_a_provider_sdk() -> None:
    offenders = []
    for module in APP.rglob("*.py"):
        rel = module.relative_to(APP).as_posix()
        if rel == CLIENT:
            continue
        for name in _imported_names(module):
            root = name.split(".")[0]
            if root in PROVIDER_SDKS:
                offenders.append(f"{rel} imports {name}")
    assert not offenders, (
        "These modules import a provider SDK directly, which breaks the model "
        f"boundary: {offenders}. Use app.generate.generate() or embed()."
    )


def test_the_public_surface_is_small() -> None:
    """Four names. A wider surface is harder to swap out."""
    import app.generate as module

    assert set(module.__all__) == {"ProviderError", "embed", "generate", "health"}


def test_callers_can_handle_failure_without_the_sdk() -> None:
    """A provider failure must be catchable without importing the SDK."""
    assert issubclass(ProviderError, RuntimeError)


def test_embed_of_nothing_calls_nothing() -> None:
    """An empty corpus must not become a network call."""
    assert embed([]) == []


def test_health_never_raises() -> None:
    ok, detail = health()
    assert isinstance(ok, bool)
    assert isinstance(detail, str)


def test_generate_is_importable_without_a_key() -> None:
    """Importing must not require credentials -- CI has none."""
    assert callable(generate)
