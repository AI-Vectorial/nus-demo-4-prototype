from __future__ import annotations

from pathlib import Path

import pytest
import tiktoken

from app.ingest.chunker import chunk_section
from app.ingest.ingester import ingest_corpus
from app.ingest.parser import parse_document
from tests.fixtures.fake_model import FakeModel


def test_parse_document_keeps_front_matter_and_section_boundaries() -> None:
    source = """---
id: travel-expense-policy
title: Travel and Expense Policy
version: "3.1"
effective: "2026-04-01"
owner: Operations
status: superseded
---
# Travel and Expense Policy

Introductory text.

## 4.1 Approval
Claims need approval.

### 4.1.1 Evidence
Keep the receipt.
"""

    document = parse_document(source)

    assert document.metadata == {
        "id": "travel-expense-policy",
        "title": "Travel and Expense Policy",
        "version": "3.1",
        "effective": "2026-04-01",
        "owner": "Operations",
        "status": "superseded",
    }
    assert [(section.heading, section.text) for section in document.sections] == [
        ("4.1 Approval", "Claims need approval."),
        ("4.1.1 Evidence", "Keep the receipt."),
    ]


def test_chunks_obey_limit_and_overlap_without_splitting_sentences() -> None:
    text = "One two three. Four five six. Seven eight nine. Ten eleven twelve."

    chunks = chunk_section(
        text,
        max_tokens=8,
        overlap_tokens=4,
        model="text-embedding-3-small",
    )

    assert chunks == [
        "One two three. Four five six.",
        "Four five six. Seven eight nine.",
        "Seven eight nine. Ten eleven twelve.",
    ]
    encoding = tiktoken.encoding_for_model("text-embedding-3-small")
    assert all(len(encoding.encode(chunk)) <= 8 for chunk in chunks)


def test_a_sentence_larger_than_the_chunk_limit_is_rejected() -> None:
    with pytest.raises(ValueError, match="sentence exceeds CHUNK_MAX_TOKENS"):
        chunk_section(
            "This sentence is much too long for a tiny chunk.",
            max_tokens=2,
            overlap_tokens=0,
            model="text-embedding-3-small",
        )


def test_ingestion_is_idempotent_and_force_recreates(
    tmp_path: Path,
    store,
) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "policy.md").write_text(
        """---
id: sample-policy
title: Sample Policy
version: "2.0"
effective: "2026-01-01"
owner: Operations
status: superseded
---
# Sample Policy

## 1. Rules
Approval needs a manager. Keep the receipt.
""",
        encoding="utf-8",
    )
    model = FakeModel()
    kwargs = {
        "max_tokens": 100,
        "overlap_tokens": 10,
        "embedding_model": "text-embedding-3-small",
        "embed_texts": model.embed,
    }

    first_count = ingest_corpus(corpus, store, **kwargs)
    first_ids = set(store._passages)
    second_count = ingest_corpus(corpus, store, **kwargs)

    assert first_count == second_count == 1
    assert set(store._passages) == first_ids
    passage = next(iter(store._passages.values()))
    assert passage.metadata == {
        "version": "2.0",
        "status": "superseded",
        "effective": "2026-01-01",
        "owner": "Operations",
    }

    (corpus / "policy.md").write_text(
        (corpus / "policy.md").read_text(encoding="utf-8").replace(
            "Keep the receipt.", "Keep all receipts."
        ),
        encoding="utf-8",
    )
    forced_count = ingest_corpus(corpus, store, force=True, **kwargs)

    assert forced_count == 1
    assert store.count() == 1
    assert set(store._passages) != first_ids


def test_ingests_all_policies_with_stable_ids_and_superseded_status(store) -> None:
    corpus = Path(__file__).resolve().parents[2] / "corpus"
    model = FakeModel()
    options = {
        "max_tokens": 400,
        "overlap_tokens": 50,
        "embedding_model": "text-embedding-3-small",
        "embed_texts": model.embed,
    }

    count = ingest_corpus(corpus, store, **options)
    ids = set(store._passages)
    again = ingest_corpus(corpus, store, **options)

    statuses = [passage.metadata["status"] for passage in store._passages.values()]
    assert count == again == store.count()
    assert len(ids) == count
    assert set(store._passages) == ids
    assert set(statuses) == {"current", "superseded"}
