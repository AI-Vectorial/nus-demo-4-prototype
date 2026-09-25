"""Ingestion: REQ-I1 to REQ-I7.

Nothing here touches the network. The corpus is the real one -- five documents
and their manifest -- but the model and the vector store are the fakes from
tests/conftest.py, so the properties being asserted are properties of the
ingest code rather than of a running Qdrant.

The two worth reading twice are idempotency and the mid-sentence rule. Both
are quietly wrong by default and both still look right when they are.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.core.config import settings
from app.ingest import pipeline
from app.ingest.chunker import (
    Chunk,
    chunk_corpus,
    chunk_document,
    passage_id,
    token_count,
)
from app.ingest.loader import CorpusError, Document, Section, load_corpus
from app.retrieve.qdrant_store import QdrantVectorStore
from app.retrieve.store import Passage
from tests.fixtures.fake_model import FakeModel
from tests.fixtures.fake_store import FakeVectorStore

# PRD section 7. Renaming any of these breaks the citation in section 5.
PAYLOAD_KEYS = {
    "text",
    "document_id",
    "document_title",
    "section",
    "version",
    "status",
    "effective",
}

_PARAGRAPH = re.compile(r"\n[ \t]*\n")


@pytest.fixture
def corpus() -> list[Document]:
    return load_corpus()


@pytest.fixture
def indexed(monkeypatch: pytest.MonkeyPatch, store: FakeVectorStore, model: FakeModel):
    """ingest(), wired to the fakes. Returns a run(force=...) callable."""
    monkeypatch.setattr(pipeline, "embed", model.embed)
    monkeypatch.setattr(pipeline, "get_vector_store", lambda: store)
    return pipeline.ingest


def _stored(store: FakeVectorStore) -> list[Passage]:
    return list(store._passages.values())


def _paragraphs(text: str) -> list[str]:
    return [part.strip() for part in _PARAGRAPH.split(text) if part.strip()]


# --- Loading --------------------------------------------------------------


def test_the_real_corpus_loads(corpus: list[Document]) -> None:
    """REQ-I1. Five documents, each with the metadata a citation needs."""
    assert len(corpus) == 5
    for document in corpus:
        assert document.id and document.title and document.owner
        assert document.version and document.effective
        assert document.status in {"current", "superseded"}
        assert document.sections


def test_sections_come_from_headings(corpus: list[Document]) -> None:
    """REQ-I2. The thing a human can check is the section number."""
    travel = next(d for d in corpus if d.file.endswith("v3.1.md"))
    headings = [section.heading for section in travel.sections]
    assert "4.2 Approval thresholds" in headings


# --- Chunking -------------------------------------------------------------


def test_every_passage_carries_the_payload(corpus: list[Document]) -> None:
    """REQ-I3 and PRD section 7, asserted on what actually reaches the store."""
    captured: list[dict] = []

    class Recorder:
        def upsert(self, collection_name: str, points: list) -> None:
            captured.extend(point.payload for point in points)

    store = QdrantVectorStore.__new__(QdrantVectorStore)
    store.collection = "test"
    store._client = Recorder()

    model = FakeModel()
    chunks = chunk_corpus(corpus)
    vectors = model.embed([chunk.text for chunk in chunks])
    store.upsert(
        [
            Passage(
                id=chunk.id,
                text=chunk.text,
                document_id=chunk.document_id,
                document_title=chunk.document_title,
                section=chunk.section,
                embedding=vector,
                metadata={
                    "version": chunk.version,
                    "status": chunk.status,
                    "effective": chunk.effective,
                },
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
    )

    assert captured
    for payload in captured:
        assert set(payload) == PAYLOAD_KEYS
        assert all(payload[key] for key in PAYLOAD_KEYS)


def test_no_passage_splits_mid_sentence(corpus: list[Document]) -> None:
    """REQ-I2, the version that would otherwise be asserted by eye.

    Every paragraph of every passage must be a whole paragraph of the source.
    Sentences in these documents are hard-wrapped across several lines, so
    "whole lines" would prove nothing -- whole paragraphs proves it.
    """
    for document in corpus:
        allowed = {section.heading for section in document.sections}
        for section in document.sections:
            allowed.update(_paragraphs(section.text))

        for chunk in chunk_document(document):
            cut = [part for part in _paragraphs(chunk.text) if part not in allowed]
            assert not cut, f"{document.file}: {chunk.section} was cut mid-paragraph: {cut}"


def test_a_long_section_splits_on_paragraphs_with_overlap() -> None:
    """The split path the real corpus never reaches -- its sections all fit."""
    paragraphs = [(f"Paragraph {index}. " + f"word{index} " * 30).strip() for index in range(14)]
    document = Document(
        file="synthetic.md",
        id="synthetic",
        title="Synthetic",
        version="1.0",
        effective="2026-01-01",
        status="current",
        owner="Nobody",
        sections=[Section(heading="1. Long", text="\n\n".join(paragraphs))],
    )

    chunks = chunk_document(document)
    assert len(chunks) > 1
    assert all(chunk.text.startswith("1. Long") for chunk in chunks)
    assert all(token_count(chunk.text) <= settings.chunk_max_tokens for chunk in chunks)

    body = set(paragraphs)
    for earlier, later in zip(chunks, chunks[1:], strict=False):
        shared = (set(_paragraphs(earlier.text)) & set(_paragraphs(later.text))) & body
        assert shared, "consecutive passages must overlap by at least one whole paragraph"


def test_passage_ids_are_a_stable_hash() -> None:
    """Thirty-two hex characters, and the same every time."""
    first = passage_id("travel-expense-policy", "4.2 Approval thresholds", "text")
    second = passage_id("travel-expense-policy", "4.2 Approval thresholds", "text")
    assert first == second
    assert re.fullmatch(r"[0-9a-f]{32}", first)
    assert first != passage_id("travel-expense-policy", "4.2 Approval thresholds", "other")


# --- The pipeline ---------------------------------------------------------


def test_ingestion_indexes_the_corpus(indexed, store: FakeVectorStore) -> None:
    """REQ-I1 from empty."""
    result = indexed()
    assert result["documents"] == 5
    assert result["passages"] == store.count() > 0
    assert result["skipped"] == 0


def test_running_twice_changes_nothing(indexed, store: FakeVectorStore) -> None:
    """REQ-I4. Same count, same ids -- the part most likely to be quietly wrong."""
    first = indexed()
    ids_after_first = {passage.id for passage in _stored(store)}
    count_after_first = store.count()

    second = indexed()

    assert store.count() == count_after_first
    assert {passage.id for passage in _stored(store)} == ids_after_first
    assert second["passages"] == first["passages"]
    assert second["skipped"] == second["passages"]


def test_force_recreates_the_collection(indexed, store: FakeVectorStore) -> None:
    """REQ-I5. The collection is emptied before anything is written back."""
    indexed()
    store.upsert(
        [
            Passage(
                id="stale",
                text="a passage from a corpus that no longer exists",
                document_id="gone",
                document_title="Gone",
                section="1. Gone",
                embedding=[0.0] * 1536,
            )
        ]
    )
    assert "stale" in {passage.id for passage in _stored(store)}

    result = indexed(force=True)

    assert "stale" not in {passage.id for passage in _stored(store)}
    assert store.count() == result["passages"]


def test_embedding_is_batched(indexed, model: FakeModel) -> None:
    """REQ-I6. One call into embed(), which batches internally."""
    indexed()
    assert len(model.embed_calls) == 1
    assert len(model.embed_calls[0]) > 1


def test_the_superseded_document_is_indexed_with_its_status(
    indexed, store: FakeVectorStore
) -> None:
    """REQ-I7. Excluding it would make "is this still current?" unanswerable."""
    indexed()

    travel = [p for p in _stored(store) if p.document_id == "travel-expense-policy"]
    versions = {p.metadata["version"]: p.metadata["status"] for p in travel}

    assert versions == {"3.1": "current", "3.0": "superseded"}
    assert any(p.metadata["status"] == "superseded" for p in _stored(store))


# --- Validation -----------------------------------------------------------

_MANIFEST = """\
documents:
  - id: travel
    file: travel.md
    title: Travel
    version: "1.0"
    effective: 2026-01-01
    owner: Group Finance
    status: current
"""

_DOCUMENT = """\
---
id: travel
title: Travel
version: "1.0"
effective: 2026-01-01
owner: Group Finance
status: current
---

## 1. Approval

Claims of 75 pounds or more require line-manager approval before reimbursement.
"""


def _corpus_dir(tmp_path: Path, *, manifest: str = _MANIFEST, **files: str) -> Path:
    (tmp_path / "MANIFEST.yaml").write_text(manifest, encoding="utf-8")
    for name, body in files.items():
        (tmp_path / f"{name}.md").write_text(body, encoding="utf-8")
    return tmp_path


def test_a_valid_corpus_passes(tmp_path: Path) -> None:
    documents = load_corpus(_corpus_dir(tmp_path, travel=_DOCUMENT))
    assert [d.file for d in documents] == ["travel.md"]


def test_a_missing_document_names_the_file(tmp_path: Path) -> None:
    with pytest.raises(CorpusError, match="travel.md"):
        load_corpus(_corpus_dir(tmp_path))


def test_an_unlisted_document_names_the_file(tmp_path: Path) -> None:
    extra = _DOCUMENT.replace("id: travel", "id: smuggled")
    with pytest.raises(CorpusError, match="smuggled.md"):
        load_corpus(_corpus_dir(tmp_path, travel=_DOCUMENT, smuggled=extra))


def test_front_matter_that_contradicts_the_manifest_names_the_file(tmp_path: Path) -> None:
    """A version the manifest disagrees with is a citation that lies."""
    wrong = _DOCUMENT.replace('version: "1.0"', 'version: "9.9"')
    with pytest.raises(CorpusError, match="travel.md"):
        load_corpus(_corpus_dir(tmp_path, travel=wrong))


def test_missing_front_matter_fields_name_the_file(tmp_path: Path) -> None:
    incomplete = _DOCUMENT.replace("owner: Group Finance\n", "")
    with pytest.raises(CorpusError, match="travel.md"):
        load_corpus(_corpus_dir(tmp_path, travel=incomplete))


def test_a_document_with_no_sections_names_the_file(tmp_path: Path) -> None:
    headless = _DOCUMENT.replace("## 1. Approval", "Approval")
    with pytest.raises(CorpusError, match="travel.md"):
        load_corpus(_corpus_dir(tmp_path, travel=headless))


def test_a_file_without_front_matter_is_not_a_policy_document(tmp_path: Path) -> None:
    """corpus/EVALUATION.md sits beside the documents and is not one of them."""
    root = _corpus_dir(tmp_path, travel=_DOCUMENT)
    (root / "EVALUATION.md").write_text("# Evaluation set\n", encoding="utf-8")
    assert len(load_corpus(root)) == 1


def test_chunks_are_typed(corpus: list[Document]) -> None:
    """A passage is a record of what was read, not a scratchpad."""
    assert Chunk.__dataclass_params__.frozen  # type: ignore[attr-defined]
    assert all(isinstance(chunk, Chunk) for chunk in chunk_corpus(corpus))
