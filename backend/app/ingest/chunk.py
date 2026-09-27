"""Policy documents into passages.

Section-first (D1): every numbered section with text of its own becomes one
passage, so a citation names something a human can open and check. Only a
section longer than CHUNK_MAX_TOKENS is split, and only between paragraphs --
never mid-sentence (REQ-I2). The piece after a split repeats whole sentences
from the end of the piece before it, up to CHUNK_OVERLAP_TOKENS.

Token counts are approximated from words rather than counted with a tokenizer:
the cap is a safety net no current section reaches, and an exact count would
need a new dependency for no change in behaviour.
"""

from __future__ import annotations

import math
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Roughly 0.75 English words per token for this family of models.
_TOKENS_PER_WORD = 4 / 3

_HEADING = re.compile(r"^(#{2,6})\s+(.+?)\s*#*\s*$")
_RULE = re.compile(r"^\s*(-{3,}|\*{3,})\s*$")
_PARAGRAPH_BREAK = re.compile(r"\n\s*\n")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")

# Stable across runs and machines, so re-ingesting produces the same ids.
_ID_NAMESPACE = uuid.UUID("5b3d6f0e-3c1a-4f0a-9f5e-7a1d2c4b8e10")


@dataclass(frozen=True)
class Document:
    """One policy document, as its front matter describes it."""

    id: str
    title: str
    version: str
    effective: str
    status: str
    owner: str
    body: str


@dataclass(frozen=True)
class Chunk:
    """One passage of one document, before it is embedded."""

    id: str
    text: str
    document_id: str
    document_title: str
    section: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def embedding_text(self) -> str:
        """What is embedded: the passage, anchored to where it came from."""
        return f"{self.document_title} — {self.section}\n\n{self.text}"


def approx_tokens(text: str) -> int:
    return math.ceil(len(text.split()) * _TOKENS_PER_WORD)


def load_corpus(directory: Path) -> list[Document]:
    """Every policy document in a directory. Files without policy front matter are skipped."""
    documents = []
    for path in sorted(directory.glob("*.md")):
        document = _parse(path.read_text(encoding="utf-8"))
        if document is not None:
            documents.append(document)
    return documents


def _parse(raw: str) -> Document | None:
    if not raw.startswith("---\n"):
        return None
    header, separator, body = raw[4:].partition("\n---\n")
    if not separator:
        return None

    fields: dict[str, str] = {}
    for line in header.splitlines():
        key, colon, value = line.partition(":")
        if colon:
            fields[key.strip()] = value.strip().strip("\"'")

    required = ("id", "title", "version", "effective", "status", "owner")
    if not all(fields.get(name) for name in required):
        return None
    return Document(body=body, **{name: fields[name] for name in required})


def chunk_document(document: Document, *, max_tokens: int, overlap_tokens: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    for section, text in _sections(document.body):
        for index, piece in enumerate(_split(text, max_tokens, overlap_tokens)):
            chunks.append(
                Chunk(
                    id=_passage_id(document, section, index, piece),
                    text=piece,
                    document_id=document.id,
                    document_title=document.title,
                    section=section,
                    metadata={
                        "version": document.version,
                        "status": document.status,
                        "effective": document.effective,
                    },
                )
            )
    return chunks


def _sections(body: str) -> list[tuple[str, str]]:
    """(heading, text) for every heading below the title that has text of its own."""
    sections: list[tuple[str, str]] = []
    heading: str | None = None
    lines: list[str] = []

    def close() -> None:
        text = "\n".join(lines).strip()
        if heading is not None and text:
            sections.append((heading, text))

    for line in body.splitlines():
        match = _HEADING.match(line)
        if match:
            close()
            heading, lines = match.group(2), []
        elif not _RULE.match(line):
            lines.append(line)
    close()
    return sections


def _split(text: str, max_tokens: int, overlap_tokens: int) -> list[str]:
    if approx_tokens(text) <= max_tokens:
        return [text]

    # A single paragraph over the cap stays whole: splitting inside it would
    # break a sentence or a table, which is worse than an oversized passage.
    pieces: list[list[str]] = [[]]
    for paragraph in (p.strip() for p in _PARAGRAPH_BREAK.split(text)):
        if not paragraph:
            continue
        current = pieces[-1]
        if current and approx_tokens("\n\n".join([*current, paragraph])) > max_tokens:
            pieces.append([paragraph])
        else:
            current.append(paragraph)

    joined = ["\n\n".join(piece) for piece in pieces]
    for index in range(1, len(joined)):
        overlap = _trailing_sentences(pieces[index - 1][-1], overlap_tokens)
        if overlap:
            joined[index] = f"{overlap}\n\n{joined[index]}"
    return joined


def _trailing_sentences(paragraph: str, budget: int) -> str:
    """As many whole sentences from the end of a paragraph as fit in the budget."""
    kept: list[str] = []
    for sentence in reversed(_SENTENCE_END.split(paragraph)):
        if approx_tokens(" ".join([sentence, *kept])) > budget:
            break
        kept.insert(0, sentence)
    return " ".join(kept)


def _passage_id(document: Document, section: str, index: int, text: str) -> str:
    key = f"{document.id}|{document.version}|{section}|{index}|{text}"
    return str(uuid.uuid5(_ID_NAMESPACE, key))
