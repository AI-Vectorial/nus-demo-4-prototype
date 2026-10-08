"""F1 -- ingest the corpus. Criteria C1, C2, C3 and C29 in tickets/T1.md.

Runs against the real corpus with the fake model and the in-memory store, so it
needs no network, no Qdrant and no key.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.ingest import corpus
from app.ingest.ingest import ensure_index, ingest, passages_for
from app.retrieve.store import Passage

CORPUS = Path(__file__).resolve().parents[2] / "corpus"

# The values table 3 decided (D1, PRD section 8). Passed in, as the command
# passes in what the environment supplies.
SETTINGS = {"max_tokens": 400, "overlap_tokens": 0, "batch_size": 96}


def run(store, model, *, force: bool = False, **overrides):
    return ingest(store, model.embed, corpus_dir=CORPUS, force=force,
                  **{**SETTINGS, **overrides})


def test_c1_every_document_is_indexed_including_the_superseded_one(store, model):
    run(store, model)

    indexed = {(p.document_id, p.metadata["version"]) for p in store._passages.values()}
    on_disk = {(d.id, d.version) for d in corpus.load(CORPUS)}
    assert indexed == on_disk
    assert ("travel-expense-policy", "3.0") in indexed


def test_c1_superseded_passages_carry_their_status(store, model):
    run(store, model)

    statuses = {p.metadata["status"] for p in store._passages.values()
                if p.metadata["version"] == "3.0"}
    assert statuses == {"superseded"}


def test_c2_running_twice_leaves_count_and_ids_unchanged(store, model):
    run(store, model)
    first = set(store._passages)
    run(store, model)

    assert set(store._passages) == first
    assert store.count() == len(first)


def test_c3_every_passage_carries_id_title_section_version_and_status(store, model):
    run(store, model)

    for p in store._passages.values():
        assert p.document_id and p.document_title and p.section
        assert p.metadata["version"] and p.metadata["status"] in {"current", "superseded"}
        assert p.metadata["effective"]


def test_two_versions_of_one_section_are_two_passages(store, model):
    run(store, model)

    thresholds = [p for p in store._passages.values()
                  if p.document_id == "travel-expense-policy"
                  and p.section.endswith("Approval thresholds")]
    assert {p.metadata["version"] for p in thresholds} == {"3.0", "3.1"}


def test_one_passage_per_section_and_heading_only_sections_are_dropped():
    documents = corpus.load(CORPUS)
    passages = passages_for(documents, max_tokens=400, overlap_tokens=0)

    with_text = sum(1 for d in documents for s in d.sections if s.text)
    assert len(passages) == with_text
    assert all(p.text for p in passages)
    assert not any(p.section == "4. Approval" for p in passages)


def test_a_passage_keeps_its_section_text_and_embeds_with_title_and_heading():
    documents = corpus.load(CORPUS)
    passage = next(p for p in passages_for(documents, max_tokens=400, overlap_tokens=0)
                   if p.section == "4.2 Approval thresholds" and p.version == "3.1")

    assert passage.text.startswith("The following thresholds apply")
    assert passage.embed_text.startswith("Travel and Expense Policy\n4.2 Approval thresholds")


def test_an_oversized_section_splits_between_sentences_never_inside_one():
    text = " ".join(f"Sentence number {i} ends here." for i in range(60))
    section = corpus.Section("9.9 Long", text)
    document = corpus.Document("doc", "Doc", "1.0", "2026-01-01", "Owner", "current", (section,))

    parts = passages_for([document], max_tokens=50, overlap_tokens=0)

    assert len(parts) > 1
    assert all(p.text.endswith(".") for p in parts)
    assert len({p.id for p in parts}) == len(parts)
    assert " ".join(p.text for p in parts) == section.text


def test_c29_force_recreates_the_collection_with_the_same_count_and_ids(store, model):
    run(store, model)
    before = set(store._passages)
    store.upsert([Passage(id="stale", text="x", document_id="gone", document_title="Gone",
                          section="1", embedding=[0.0] * model.embedding_dimensions)])

    run(store, model, force=True)

    assert set(store._passages) == before


def test_c29_force_re_embeds_every_passage(store, model):
    run(store, model)
    model.embed_calls.clear()

    run(store, model, force=True)

    assert sum(len(call) for call in model.embed_calls) == store.count()


@pytest.mark.parametrize("batch_size", [96, 10])
def test_c29_embedding_requests_are_batched(store, model, batch_size):
    run(store, model, batch_size=batch_size)

    assert len(model.embed_calls) < store.count()
    assert all(len(call) <= batch_size for call in model.embed_calls)


# --- the deployed service builds its own index on boot ---------------------------

def ensure(store, model, dimensions=1536):
    return ensure_index(store, model.embed, corpus_dir=CORPUS, dimensions=dimensions,
                        **SETTINGS)


def test_an_empty_store_is_indexed_on_boot(store, model):
    status = ensure(store, model)

    assert status.startswith("index rebuilt")
    assert store.count() == len(passages_for(corpus.load(CORPUS), max_tokens=400,
                                             overlap_tokens=0))


def test_a_current_index_is_left_alone(store, model):
    ensure(store, model)
    model.embed_calls.clear()

    status = ensure(store, model)

    assert status.startswith("index current")
    assert model.embed_calls == []


def test_an_index_at_another_dimension_is_rebuilt(model):
    from tests.fixtures.fake_store import FakeVectorStore

    old = FakeVectorStore(dim=3072)
    old.ensure_ready()

    status = ensure(old, model, dimensions=1536)

    assert "had 0 passages at 3072" in status
    assert old.dimension() == 1536


def test_an_index_with_stale_passages_is_rebuilt(store, model):
    ensure(store, model)
    store.upsert([Passage(id="stale", text="x", document_id="gone", document_title="Gone",
                          section="1", embedding=[0.0] * model.embedding_dimensions)])

    ensure(store, model)

    assert "stale" not in store._passages
