"""Corpus to passages to vectors (F1).

One passage per section (D1). A section longer than CHUNK_MAX_TOKENS -- none is,
today -- is split between sentences, never inside one (REQ-I2).

A passage id is derived from document, version and section, so running ingest
again replaces each passage with itself (REQ-I4), and the two versions of the
travel policy never overwrite each other.
"""

from __future__ import annotations

import logging
import math
import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.ingest import corpus
from app.retrieve.store import Passage, VectorStore

log = logging.getLogger(__name__)

# Tokens per word for English prose. An estimate is enough: the ceiling is a
# guard, not a tokenizer (D1 -- the team chose not to add one).
_TOKENS_PER_WORD = 4 / 3
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class Chunk:
    """A passage before it has been embedded."""

    id: str
    text: str
    embed_text: str
    document_id: str
    document_title: str
    section: str
    version: str
    status: str
    effective: str


@dataclass(frozen=True)
class IngestReport:
    documents: int
    passages: int
    requests: int


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text.split()) * _TOKENS_PER_WORD)


def _split(text: str, max_tokens: int, overlap_tokens: int) -> list[str]:
    """Whole sentences, packed up to max_tokens. A sentence longer than the
    ceiling stays whole: cutting it would lose the clause that gives it meaning."""
    if estimate_tokens(text) <= max_tokens:
        return [text]
    parts: list[list[str]] = [[]]
    for sentence in _SENTENCE_END.split(text):
        current = parts[-1]
        if current and estimate_tokens(" ".join([*current, sentence])) > max_tokens:
            carried: list[str] = []
            for previous in reversed(current):
                if estimate_tokens(" ".join([previous, *carried])) > overlap_tokens:
                    break
                carried.insert(0, previous)
            parts.append(carried)
        parts[-1].append(sentence)
    return [" ".join(part) for part in parts]


def _id(document: corpus.Document, section: str, part: int) -> str:
    key = f"{document.id}|{document.version}|{section}|{part}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, key))


def passages_for(documents: list[corpus.Document], *, max_tokens: int,
                 overlap_tokens: int) -> list[Chunk]:
    chunks = []
    for document in documents:
        for section in document.sections:
            if not section.text:
                continue  # a heading with nothing under it
            for part, text in enumerate(_split(section.text, max_tokens, overlap_tokens)):
                chunks.append(Chunk(
                    id=_id(document, section.heading, part),
                    text=text,
                    embed_text=f"{document.title}\n{section.heading}\n\n{text}",
                    document_id=document.id,
                    document_title=document.title,
                    section=section.heading,
                    version=document.version,
                    status=document.status,
                    effective=document.effective,
                ))
    return chunks


def ingest(store: VectorStore, embed: Callable[[list[str]], list[list[float]]], *,
           corpus_dir: Path, max_tokens: int, overlap_tokens: int, batch_size: int,
           force: bool = False) -> IngestReport:
    documents = corpus.load(corpus_dir)
    chunks = passages_for(documents, max_tokens=max_tokens, overlap_tokens=overlap_tokens)

    if force:
        store.reset()
    store.ensure_ready()

    requests = 0
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]
        vectors = embed([c.embed_text for c in batch])
        requests += 1
        store.upsert([
            Passage(
                id=c.id,
                text=c.text,
                document_id=c.document_id,
                document_title=c.document_title,
                section=c.section,
                embedding=vector,
                metadata={"version": c.version, "status": c.status, "effective": c.effective},
            )
            for c, vector in zip(batch, vectors, strict=True)
        ])

    log.info("ingested %d documents, %d passages, %d embedding requests",
             len(documents), len(chunks), requests)
    return IngestReport(len(documents), len(chunks), requests)
