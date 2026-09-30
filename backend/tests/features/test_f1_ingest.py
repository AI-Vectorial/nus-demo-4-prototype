"""F1 -- ingest the corpus. Epic criteria 1 to 6.

Runs over the real corpus in backend/corpus/, with the fake model and the
in-memory store, so it needs no network and no Qdrant.
"""

from __future__ import annotations

import math
import re

import pytest

from app.core.config import settings
from app.ingest import CORPUS_DIR, ingest
from app.ingest.chunker import approx_tokens, split
from app.ingest.loader import load_corpus, parse_document

PAYLOAD_FIELDS = ("text", "document_id", "document_title", "section", "version", "status",
                  "effective")


def _all(store):
    return list(store._passages.values())


def _payload(passage) -> dict:
    return {
        "text": passage.text,
        "document_id": passage.document_id,
        "document_title": passage.document_title,
        "section": passage.section,
        **passage.metadata,
    }


@pytest.fixture
def indexed(store, model):
    ingest(store, model.embed)
    return store


# --------------------------------------------------------------- criterion 1


def test_every_corpus_file_is_indexed_from_empty(store, model):
    """REQ-I1, REQ-I7 -- all five files, including the superseded one."""
    assert store.count() == 0

    count = ingest(store, model.embed)

    assert count == store.count() > 0
    indexed = {(p.document_id, p.metadata["version"]) for p in _all(store)}
    files = {(d.id, d.version) for d in load_corpus(CORPUS_DIR)}
    assert len(files) == 5
    assert indexed == files


def test_the_superseded_travel_policy_is_indexed_with_its_status(indexed):
    """REQ-I7 -- indexed, not excluded."""
    v30 = [p for p in _all(indexed)
           if p.document_id == "travel-expense-policy" and p.metadata["version"] == "3.0"]
    assert v30
    assert {p.metadata["status"] for p in v30} == {"superseded"}


# --------------------------------------------------------------- criterion 2


def test_every_passage_carries_the_citation_payload(indexed):
    """REQ-I3 -- PRD section 7, every field present and non-empty."""
    for passage in _all(indexed):
        payload = _payload(passage)
        missing = [f for f in PAYLOAD_FIELDS if not str(payload.get(f, "")).strip()]
        assert not missing, f"{passage.section} is missing {missing}"


# --------------------------------------------------------------- criterion 3


def test_running_ingest_twice_changes_nothing(store, model):
    """REQ-I4 -- same count, same ids."""
    ingest(store, model.embed)
    first = set(store._passages)

    ingest(store, model.embed)

    assert set(store._passages) == first
    assert store.count() == len(first)


# --------------------------------------------------------------- criterion 4


def test_force_recreates_and_reembeds_with_the_same_ids(store, model):
    """REQ-I5 -- a stray passage is gone, everything is embedded again."""
    ingest(store, model.embed)
    original = set(store._passages)
    stray = next(iter(store._passages.values()))
    store._passages["stray"] = stray
    model.embed_calls.clear()

    ingest(store, model.embed, force=True)

    assert set(store._passages) == original
    assert sum(len(call) for call in model.embed_calls) == len(original)


# --------------------------------------------------------------- criterion 5


def test_no_passage_crosses_a_section_boundary(indexed):
    """REQ-I2 -- a passage never contains a heading."""
    for passage in _all(indexed):
        assert not re.search(r"^#{1,6} ", passage.text, re.M), passage.section


def test_an_oversized_section_splits_only_at_sentence_ends():
    """REQ-I2 -- when the cap bites, every piece ends a sentence."""
    text = " ".join(f"Sentence number {n} says something about approval." for n in range(40))

    pieces = split(text, max_tokens=30, overlap_tokens=0)

    assert len(pieces) > 1
    for piece in pieces:
        assert piece.endswith("."), piece
        assert approx_tokens(piece) <= 30
    assert " ".join(pieces) == text


def test_a_section_under_the_cap_is_kept_whole():
    """D1 -- one passage per section when it fits."""
    text = "Claims of £75 or more require approval. A claim of exactly £75 does too."
    assert split(text, max_tokens=512, overlap_tokens=0) == [text]


def test_every_real_section_fits_under_the_configured_cap(indexed):
    """D1's premise: at CHUNK_MAX_TOKENS, no real section needs splitting."""
    sections = [(p.document_id, p.metadata["version"], p.section) for p in _all(indexed)]
    assert len(sections) == len(set(sections))


def test_headings_with_no_text_of_their_own_are_skipped():
    doc = parse_document(
        "---\nid: x\ntitle: X\nversion: \"1\"\neffective: 2026-01-01\n"
        "owner: O\nstatus: current\n---\n\n# X\n\n## 4. Approval\n\n"
        "### 4.2 Approval thresholds\n\nClaims need approval.\n"
    )
    assert [(s.parent, s.heading) for s in doc.sections] == [
        ("4. Approval", "4.2 Approval thresholds")
    ]


# --------------------------------------------------------------- criterion 6


def test_embedding_calls_are_batched(store, model):
    """REQ-I6 -- at most ceil(passages / EMBEDDING_BATCH_SIZE) calls."""
    count = ingest(store, model.embed, batch_size=7)

    assert len(model.embed_calls) <= math.ceil(count / 7)
    assert all(len(call) <= 7 for call in model.embed_calls)


def test_the_batch_size_defaults_to_configuration(store, model):
    count = ingest(store, model.embed)

    assert len(model.embed_calls) == math.ceil(count / settings.embedding_batch_size)
