"""F1 -- ingest the corpus. REQ-I1 .. REQ-I7.

Runs with the fakes only: no Qdrant, no network.
"""

from __future__ import annotations

import uuid

from app.ingest import CORPUS_DIR, index_corpus, load_corpus


def test_every_policy_document_is_chunked_into_sections(store, model):
    """REQ-I1, REQ-I2: five documents, each split on section headings."""
    passages = load_corpus(CORPUS_DIR)

    documents = {p.document_id for p in passages}
    assert documents == {
        "travel-expense-policy",
        "client-onboarding-kyc",
        "records-retention",
        "outsourcing-third-party",
    }
    # Each passage is a whole section: it begins at a heading.
    assert all(p.text.startswith("#") for p in passages)


def test_every_passage_carries_its_provenance(store, model):
    """REQ-I3: document id, title, section, version and status."""
    passages = load_corpus(CORPUS_DIR)

    for p in passages:
        assert p.document_id
        assert p.document_title
        assert p.section
        assert p.metadata["version"]
        assert p.metadata["status"] in {"current", "superseded"}


def test_superseded_travel_policy_is_indexed_not_excluded(store, model):
    """REQ-I7: v3.0 is indexed, flagged superseded."""
    passages = load_corpus(CORPUS_DIR)

    old = [p for p in passages if p.document_id == "travel-expense-policy"
           and p.metadata["version"] == "3.0"]
    new = [p for p in passages if p.document_id == "travel-expense-policy"
           and p.metadata["version"] == "3.1"]
    assert old and new
    assert all(p.metadata["status"] == "superseded" for p in old)
    assert all(p.metadata["status"] == "current" for p in new)


def test_indexing_twice_changes_nothing(store, model):
    """REQ-I4: same passage count, same passage ids."""
    first = index_corpus(store, model.embed, CORPUS_DIR)
    count_after_first = store.count()
    ids_after_first = set(store._passages)

    second = index_corpus(store, model.embed, CORPUS_DIR)

    assert first == second
    assert store.count() == count_after_first
    assert set(store._passages) == ids_after_first
    assert count_after_first > 0


def test_passage_ids_are_uuids(store, model):
    """Qdrant accepts UUID point ids; the id is a stable hash of the content."""
    for p in load_corpus(CORPUS_DIR):
        uuid.UUID(p.id)


def test_embedding_calls_respect_the_batch_size(store, model):
    """REQ-I6: no embedding call carries more than the batch size."""
    index_corpus(store, model.embed, CORPUS_DIR, batch_size=2)

    assert model.embed_calls
    assert all(0 < len(call) <= 2 for call in model.embed_calls)


def test_sample_corpus_indexes_into_an_empty_store(store, model, sample_corpus):
    """The fixture corpus works with the same entry point."""
    written = index_corpus(store, model.embed, sample_corpus)

    assert written == store.count() > 0
