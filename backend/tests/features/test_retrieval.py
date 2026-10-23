from __future__ import annotations

from app.retrieve.query import retrieve_candidates


def test_retrieve_candidates_returns_the_matching_policy(loaded_store, model) -> None:
    hits = retrieve_candidates(
        "What is the approval threshold for expenses?",
        store=loaded_store,
        embed_texts=model.embed,
        limit=3,
    )

    assert hits
    assert hits[0].document_id == "travel-expense-policy"
    assert "75" in hits[0].text
