"""Sections into passages.

The section is the unit (D1). Policy is already written in numbered sections,
and a citation to "4.2 Approval thresholds" is something a human can open the
document and check -- which an offset into a 400-token window is not.

Two rules bend that, and only two. A section longer than CHUNK_MAX_TOKENS is
split on paragraph boundaries with CHUNK_OVERLAP_TOKENS carried over, so a
clause never loses the sentence that qualified it. A section shorter than
CHUNK_MIN_TOKENS merges forward, because `## 4. Approval` followed straight
away by `### 4.1 ...` would otherwise be indexed as a passage whose entire
content is its own title.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from app.core.config import settings
from app.ingest.loader import Document, Section

# Words to tokens, approximately. Approximate on purpose: a real tokeniser is
# a dependency, and worse, it moves. Chunk boundaries decide passage ids, and
# ids that change when a library is upgraded would quietly break REQ-I4.
_TOKENS_PER_WORD = 1.3

_PARAGRAPH = re.compile(r"\n[ \t]*\n")


@dataclass(frozen=True)
class Chunk:
    """One passage's worth of text, with the metadata a citation needs."""

    id: str
    text: str
    document_id: str
    document_title: str
    section: str
    version: str
    status: str
    effective: str


def token_count(text: str) -> int:
    """Roughly how many tokens `text` is worth."""
    return int(len(text.split()) * _TOKENS_PER_WORD)


def passage_id(document_id: str, section: str, text: str) -> str:
    """A stable id, so re-running ingestion replaces rather than duplicates.

    This is what makes REQ-I4 fall out for free: identical input yields an
    identical id, the upsert overwrites the point that is already there, and
    the passage count does not move. Thirty-two hex characters because that is
    also a valid Qdrant point id.
    """
    digest = hashlib.sha256(f"{document_id}\n{section}\n{text}".encode())
    return digest.hexdigest()[:32]


def chunk_document(document: Document) -> list[Chunk]:
    """Every passage for one document, in document order."""
    chunks: list[Chunk] = []
    for section in _merge_short(document.sections):
        for text in _split(section):
            chunks.append(
                Chunk(
                    id=passage_id(document.id, section.heading, text),
                    text=text,
                    document_id=document.id,
                    document_title=document.title,
                    section=section.heading,
                    version=document.version,
                    status=document.status,
                    effective=document.effective,
                )
            )
    return chunks


def chunk_corpus(documents: list[Document]) -> list[Chunk]:
    """Every passage for every document."""
    return [chunk for document in documents for chunk in chunk_document(document)]


def _merge_short(sections: list[Section]) -> list[Section]:
    """Fold sections shorter than the minimum into the one that follows."""
    merged: list[Section] = []
    pending: list[Section] = []

    for section in sections:
        pending.append(section)
        combined = _combine(pending)
        if _tokens(combined) >= settings.chunk_min_tokens:
            merged.append(combined)
            pending = []

    if pending:
        # Nothing follows it in this document, so a short tail stands alone.
        merged.append(_combine(pending))
    return merged


def _combine(sections: list[Section]) -> Section:
    """One section from several, labelled by whichever contributed the most.

    Not by the first, which is the tempting choice and the wrong one: `## 4.
    Approval` carries no text at all, so labelling the merged passage with it
    would cite a container and lose "4.2 Approval thresholds" -- the section
    the evaluation set expects a reader to be sent to. Every swallowed heading
    stays in the body, so nothing searchable is lost either way.
    """
    if len(sections) == 1:
        return sections[0]

    longest = max(sections, key=lambda section: len(section.text))
    parts: list[str] = []
    for section in sections:
        if section is not longest:
            # Its own heading is prepended once, by _passage_text.
            parts.append(section.heading)
        if section.text:
            parts.append(section.text)

    return Section(heading=longest.heading, text="\n\n".join(parts))


def _split(section: Section) -> list[str]:
    """Passage texts for one section, each carrying the heading it came from.

    The heading rides along because a table of amounts is close to meaningless
    without the words "Approval thresholds" above it, and the embedding only
    sees the text.
    """
    whole = _passage_text(section.heading, [section.text] if section.text else [])
    if token_count(whole) <= settings.chunk_max_tokens:
        return [whole]

    paragraphs = [p.strip() for p in _PARAGRAPH.split(section.text) if p.strip()]
    budget = max(settings.chunk_max_tokens - token_count(section.heading), 1)

    texts: list[str] = []
    window: list[str] = []
    for paragraph in paragraphs:
        if window and token_count("\n\n".join([*window, paragraph])) > budget:
            texts.append(_passage_text(section.heading, window))
            window = _overlap(window)
        window.append(paragraph)

    if window:
        texts.append(_passage_text(section.heading, window))
    return texts


def _overlap(window: list[str]) -> list[str]:
    """The tail of one passage, repeated at the head of the next.

    Whole paragraphs only. Overlapping by a token count would put half a
    sentence at the start of a passage, which is the thing REQ-I2 forbids.
    """
    carried: list[str] = []
    for paragraph in reversed(window):
        if token_count("\n\n".join([paragraph, *carried])) > settings.chunk_overlap_tokens:
            break
        carried.insert(0, paragraph)
    return carried


def _passage_text(heading: str, paragraphs: list[str]) -> str:
    return "\n\n".join([heading, *paragraphs])


def _tokens(section: Section) -> int:
    return token_count(_passage_text(section.heading, [section.text] if section.text else []))
