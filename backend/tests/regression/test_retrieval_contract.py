"""The retrieval contract.

Retrieval is reached through app.retrieve.store.VectorStore, and exactly one
module knows which engine is underneath. These tests keep it that way, because
an architectural boundary that is only written down in a comment stops being
true the first time someone is in a hurry.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.retrieve import get_vector_store
from app.retrieve.qdrant_store import QdrantVectorStore
from app.retrieve.store import Hit, Passage, VectorStore

APP = Path(__file__).resolve().parents[2] / "app"

# The one module allowed to import the client library.
STORE_IMPL = "retrieve/qdrant_store.py"


def _imported_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_only_the_implementation_imports_the_client() -> None:
    """No module outside the store implementation may import qdrant_client."""
    offenders = [
        module.relative_to(APP).as_posix()
        for module in APP.rglob("*.py")
        if module.relative_to(APP).as_posix() != STORE_IMPL
        and any(name.startswith("qdrant_client") for name in _imported_names(module))
    ]
    assert not offenders, (
        "These modules import the client library directly, which breaks the "
        f"retrieval boundary: {offenders}. Use app.retrieve.get_vector_store()."
    )


def test_implementation_satisfies_the_interface() -> None:
    store = QdrantVectorStore.__new__(QdrantVectorStore)
    assert isinstance(store, VectorStore)


def test_interface_is_expressed_in_domain_types() -> None:
    """No vendor type may appear in the interface's signatures."""
    source = (APP / "retrieve" / "store.py").read_text(encoding="utf-8")
    assert "qdrant" not in source.lower()


def test_every_interface_method_is_implemented() -> None:
    required = {"ensure_ready", "upsert", "search", "count", "health"}
    missing = required - set(dir(QdrantVectorStore))
    assert not missing, f"QdrantVectorStore is missing: {missing}"


def test_get_vector_store_is_cached() -> None:
    """One client, reused -- not a new connection per call."""
    assert get_vector_store() is get_vector_store()


@pytest.mark.parametrize("model", [Passage, Hit])
def test_domain_types_are_immutable(model: type) -> None:
    """A retrieved passage is a record of what was found, not a scratchpad."""
    assert model.__dataclass_params__.frozen  # type: ignore[attr-defined]
