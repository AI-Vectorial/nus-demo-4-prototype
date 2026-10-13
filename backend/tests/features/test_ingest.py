"""F1 -- ingest the corpus. REQ-I1 .. REQ-I7.

Chunking is tested against the fixture corpus and against the real one, read
only. Ingestion is tested end to end with the fake store and fake model, so
"running it twice changes nothing" is asserted, not assumed.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.generate import client as provider
from app.ingest.__main__ import ingest
from app.ingest.chunk import approx_tokens, chunk_document, load_corpus

REAL_CORPUS = Path(__file__).resolve().parents[2] / "corpus"

MAX_TOKENS = 400
OVERLAP_TOKENS = 60


def _chunks(directory: Path, max_tokens: int = MAX_TOKENS, overlap: int = OVERLAP_TOKENS):
    return [
        chunk
        for document in load_corpus(directory)
        for chunk in chunk_document(document, max_tokens=max_tokens, overlap_tokens=overlap)
    ]


# --- chunking: REQ-I2, REQ-I3, REQ-I7 ----------------------------------------


def test_a_section_becomes_one_passage_with_its_own_text_only(sample_corpus):
    chunks = {
        c.section: c for c in _chunks(sample_corpus) if c.document_id == "travel-expense-policy"
    }

    approval = chunks["4.2 Approval thresholds"]
    assert "Claims of 75 pounds or more" in approval.text
    assert "exactly 75 pounds requires approval" in approval.text
    assert "London" not in approval.text


def test_every_passage_carries_id_title_section_version_and_status(sample_corpus):
    for chunk in _chunks(sample_corpus):
        assert chunk.document_id
        assert chunk.document_title
        assert chunk.section
        assert chunk.metadata["version"]
        assert chunk.metadata["status"] in {"current", "superseded"}
        assert chunk.metadata["effective"]


def test_only_policy_documents_are_loaded_from_the_real_corpus():
    documents = load_corpus(REAL_CORPUS)

    # EVALUATION.md, FICTION-AUDIT.md and MANIFEST.yaml carry no policy front matter.
    assert sorted((d.id, d.version) for d in documents) == [
        ("client-onboarding-kyc", "2.4"),
        ("outsourcing-third-party", "1.8"),
        ("records-retention", "4.0"),
        ("travel-expense-policy", "3.0"),
        ("travel-expense-policy", "3.1"),
    ]


def test_the_superseded_policy_is_indexed_and_marked_superseded():
    by_version = {}
    for chunk in _chunks(REAL_CORPUS):
        if chunk.document_id == "travel-expense-policy":
            by_version.setdefault(chunk.metadata["version"], set()).add(chunk.metadata["status"])

    assert by_version == {"3.0": {"superseded"}, "3.1": {"current"}}


def test_the_real_approval_section_is_one_whole_passage():
    approval = [
        c for c in _chunks(REAL_CORPUS)
        if c.metadata["version"] == "3.1" and c.section == "4.2 Approval thresholds"
    ]

    assert len(approval) == 1
    assert "A claim of exactly £75 requires line-manager approval" in approval[0].text


def test_a_heading_with_no_text_of_its_own_is_not_a_passage():
    # "## 4. Approval" is followed directly by "### 4.1 ...".
    sections = {c.section for c in _chunks(REAL_CORPUS) if c.metadata["version"] == "3.1"}

    assert "4. Approval" not in sections
    assert "4.1 General principle" in sections


def test_same_section_in_two_versions_gets_two_different_ids():
    ids = [c.id for c in _chunks(REAL_CORPUS)]

    assert len(ids) == len(set(ids))


# --- splitting a long section: D1, REQ-I2 ------------------------------------


def _long_document(tmp_path: Path) -> Path:
    paragraphs = [
        " ".join(f"Paragraph {p} sentence {s} states a rule about claims." for s in range(12))
        for p in range(6)
    ]
    body = "\n\n".join(paragraphs)
    (tmp_path / "long.md").write_text(
        "---\nid: long\ntitle: Long Policy\nversion: \"1.0\"\neffective: 2026-01-01\n"
        "owner: Group Finance\nstatus: current\n---\n\n"
        f"# Long Policy\n\n## 1. Everything\n\n{body}\n",
        encoding="utf-8",
    )
    return tmp_path


def test_a_section_over_the_cap_splits_on_paragraph_boundaries(tmp_path):
    chunks = _chunks(_long_document(tmp_path), max_tokens=200, overlap=30)

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.section == "1. Everything"
        assert approx_tokens(chunk.text) <= 200 + 30
        # Never mid-sentence: each piece starts at a sentence and ends at one.
        assert chunk.text.startswith("Paragraph")
        assert chunk.text.endswith(".")


def test_the_next_piece_repeats_whole_sentences_from_the_last(tmp_path):
    first, second, *_ = _chunks(_long_document(tmp_path), max_tokens=200, overlap=30)

    opening = second.text.split(". ")[0] + "."
    assert opening in first.text
    assert 0 < approx_tokens(second.text.split("\n\n")[0]) <= 30


def test_no_real_section_exceeds_the_cap():
    # D1 relies on this: the corpus is cited by section, and today nothing splits.
    for chunk in _chunks(REAL_CORPUS):
        assert approx_tokens(chunk.text) <= MAX_TOKENS, chunk.section


# --- running it: REQ-I1, REQ-I4, REQ-I5 --------------------------------------


def test_ingest_indexes_the_corpus_from_empty(sample_corpus, store, model):
    result = ingest(sample_corpus, store=store, embed=model.embed,
                    max_tokens=MAX_TOKENS, overlap_tokens=OVERLAP_TOKENS)

    assert result.indexed == store.count() > 0


def test_running_ingest_twice_changes_nothing(sample_corpus, store, model):
    kwargs = dict(store=store, embed=model.embed, max_tokens=MAX_TOKENS,
                  overlap_tokens=OVERLAP_TOKENS)
    ingest(sample_corpus, **kwargs)
    count, ids = store.count(), set(store._passages)

    ingest(sample_corpus, **kwargs)

    assert store.count() == count
    assert set(store._passages) == ids


def test_force_recreates_the_collection_and_re_embeds_everything(sample_corpus, store, model):
    kwargs = dict(store=store, embed=model.embed, max_tokens=MAX_TOKENS,
                  overlap_tokens=OVERLAP_TOKENS)
    ingest(sample_corpus, **kwargs)
    store.upsert([replace(next(iter(store._passages.values())), id="stale")])

    result = ingest(sample_corpus, force=True, **kwargs)

    assert "stale" not in store._passages
    assert store.recreated
    assert result.indexed == store.count()
    assert len(model.embed_calls[-1]) == result.indexed


def test_the_passage_is_embedded_with_its_section_heading_not_its_title(
    sample_corpus, store, model
):
    ingest(sample_corpus, store=store, embed=model.embed,
           max_tokens=MAX_TOKENS, overlap_tokens=OVERLAP_TOKENS)

    embedded = model.embed_calls[-1]
    assert any(text.startswith("4.2 Approval thresholds\n\nClaims of 75") for text in embedded)
    assert not any(text.startswith("Travel and Expense Policy") for text in embedded)


# --- batching: REQ-I6 --------------------------------------------------------


def test_embedding_calls_are_batched(monkeypatch):
    sizes: list[int] = []

    class FakeEmbeddings:
        def create(self, *, model, input):
            sizes.append(len(input))
            return SimpleNamespace(data=[SimpleNamespace(embedding=[0.0] * 4) for _ in input])

    monkeypatch.setattr(provider, "settings", replace(
        provider.settings, embedding_batch_size=3, embedding_dimensions=4,
    ))
    monkeypatch.setattr(provider, "_client", lambda: SimpleNamespace(embeddings=FakeEmbeddings()))

    vectors = provider.embed([f"text {i}" for i in range(7)])

    assert sizes == [3, 3, 1]
    assert len(vectors) == 7


@pytest.mark.parametrize("flag", ["--force"])
def test_the_command_accepts_force(flag):
    from app.ingest.__main__ import parse_args

    assert parse_args([flag]).force is True
    assert parse_args([]).force is False
