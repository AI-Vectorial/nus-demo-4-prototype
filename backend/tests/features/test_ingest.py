"""F1 -- ingest the corpus. REQ-I1 to REQ-I7.

These are the acceptance tests for the ingest feature. They run against the
in-memory store and the fake model, so they need no Qdrant and no network.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from app.core.config import settings
from app.generate import client as provider_client
from app.ingest import build_passages, ingest, read_documents, split_sections, split_text
from tests.fixtures.fake_model import FakeModel
from tests.fixtures.fake_store import FakeVectorStore

REAL_CORPUS = Path(__file__).resolve().parents[2] / "corpus"
FIXTURE_CORPUS = Path(__file__).resolve().parents[1] / "fixtures" / "corpus"


# REQ-I2 -- split on section boundaries, never mid-sentence


def test_sections_are_split_on_headings():
    body = (
        "## 4. Approval\n\n"
        "### 4.1 General principle\n\nAll claims need approval.\n\n"
        "### 4.2 Thresholds\n\nClaims of 75 or more need approval.\n"
    )

    sections = split_sections(body)

    assert [heading for heading, _ in sections] == ["4.1 General principle", "4.2 Thresholds"]
    assert "All claims need approval." in sections[0][1]
    assert "Claims of 75 or more" in sections[1][1]


def test_a_paragraph_is_never_cut_across_chunks():
    paragraphs = [
        "Claims of 75 pounds or more need line-manager approval.",
        "A claim of exactly 75 pounds also needs approval.",
        "Claims under 75 pounds do not need approval.",
    ]
    text = "\n\n".join(paragraphs)

    chunks = split_text(text, max_chars=60)

    for paragraph in paragraphs:
        assert sum(paragraph in chunk for chunk in chunks) == 1
    assert all(len(chunk) <= 60 for chunk in chunks)


def test_markdown_tables_keep_their_line_structure():
    table = "| Band | Cap |\n| --- | --- |\n| Singapore | 300 |"

    chunks = split_text(table, max_chars=500)

    assert chunks == [table]


# REQ-I3 -- every passage carries its document id, title, section, version, status


def test_every_passage_carries_its_provenance(store: FakeVectorStore, model: FakeModel):
    ingest(store, model.embed, FIXTURE_CORPUS)

    passages = build_passages(read_documents(FIXTURE_CORPUS), model.embed)

    assert passages
    for passage in passages:
        assert passage.document_id
        assert passage.document_title
        assert passage.section
        assert passage.metadata["version"]
        assert passage.metadata["status"] in {"current", "superseded"}


# REQ-I4 -- re-running changes nothing


def test_running_twice_leaves_the_count_and_ids_unchanged(store: FakeVectorStore, model: FakeModel):
    first = ingest(store, model.embed, FIXTURE_CORPUS)
    count_after_first = store.count()

    second = ingest(store, model.embed, FIXTURE_CORPUS)

    assert second.passages == first.passages
    assert store.count() == count_after_first


def test_passage_ids_are_stable_across_runs(model: FakeModel):
    documents = read_documents(FIXTURE_CORPUS)

    first = build_passages(documents, model.embed)
    second = build_passages(documents, model.embed)

    assert [p.id for p in first] == [p.id for p in second]


# REQ-I5 -- --force recreates the collection and re-embeds everything


def test_force_recreates_the_collection(store: FakeVectorStore, model: FakeModel):
    ingest(store, model.embed, FIXTURE_CORPUS)
    count_before = store.count()
    embed_calls_before = len(model.embed_calls)

    ingest(store, model.embed, FIXTURE_CORPUS, force=True)

    assert store.count() == count_before
    assert len(model.embed_calls) > embed_calls_before


# REQ-I6 -- embedding calls are batched


def test_embedding_requests_are_split_into_batches(monkeypatch):
    requests: list[list[str]] = []

    class FakeEmbeddings:
        def create(self, model, input):  # noqa: A002 - the SDK's own parameter name
            requests.append(list(input))
            vector = [0.0] * settings.embedding_dimensions
            return SimpleNamespace(data=[SimpleNamespace(embedding=vector) for _ in input])

    fake_sdk = SimpleNamespace(embeddings=FakeEmbeddings())
    monkeypatch.setattr(provider_client, "_client", lambda: fake_sdk)

    vectors = provider_client.embed([f"passage {i}" for i in range(5)], batch_size=2)

    assert len(vectors) == 5
    assert [len(batch) for batch in requests] == [2, 2, 1]


# REQ-I7 -- superseded documents are indexed WITH their status, not excluded


def test_superseded_policy_is_indexed_and_flagged(model: FakeModel):
    passages = build_passages(read_documents(REAL_CORPUS), model.embed)

    statuses = {p.metadata["status"] for p in passages if p.document_id == "travel-expense-policy"}
    versions = {p.metadata["version"] for p in passages if p.document_id == "travel-expense-policy"}

    assert statuses == {"current", "superseded"}
    assert versions == {"3.0", "3.1"}


def test_the_corpus_yields_five_policies():
    documents = read_documents(REAL_CORPUS)

    assert len(documents) == 5
    assert "EVALUATION" not in {d.path.stem for d in documents}


# REQ-I1 -- indexes the whole corpus from empty


def test_ingest_from_empty_indexes_every_document(store: FakeVectorStore, model: FakeModel):
    result = ingest(store, model.embed, FIXTURE_CORPUS)

    assert result.documents == len(read_documents(FIXTURE_CORPUS))
    assert store.count() == result.passages > 0
