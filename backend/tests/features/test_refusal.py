from __future__ import annotations

from app.retrieve.query import Grounded, Insufficient, retrieve


def test_supported_query_returns_grounded_passages(loaded_store, model) -> None:
    result = retrieve(
        "What is the approval threshold?",
        store=loaded_store,
        embed_texts=model.embed,
        min_score=0.1,
        limit=3,
    )

    assert isinstance(result, Grounded)
    assert result.hits[0].document_id == "travel-expense-policy"


def test_unsupported_query_returns_explicit_insufficiency_without_generation(
    loaded_store, model
) -> None:
    result = retrieve(
        "What is my parental leave entitlement?",
        store=loaded_store,
        embed_texts=model.embed,
        min_score=0.99,
        limit=3,
    )

    assert isinstance(result, Insufficient)
    assert model.generate_calls == []
