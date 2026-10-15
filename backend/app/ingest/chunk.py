"""Splitting a policy document into passages.

Split on section headings first, then on paragraphs, so a passage never starts
or ends in the middle of a paragraph. Markdown line structure is kept, so a
table stays a table (REQ-U12).

Length is approximate. Tokens are estimated from characters, with no tokenizer
dependency (plan amendment 1). A limit is a target, not an exact count.
"""

from __future__ import annotations

import re

CHARS_PER_TOKEN = 4

_HEADING = re.compile(r"^(#{2,3})\s+(.+?)\s*$")
_PARAGRAPH_BREAK = re.compile(r"\n\s*\n")


def split_sections(body: str) -> list[tuple[str, str]]:
    """Return (heading, text) for each section that has text under it.

    Level 2 and level 3 headings both start a section, so a section citation
    names the heading as written, e.g. "4.2 Approval thresholds". The document
    title (level 1) is not a section.
    """
    sections: list[tuple[str, list[str]]] = []
    current: list[str] | None = None

    for line in body.splitlines():
        heading = _HEADING.match(line)
        if heading:
            current = []
            sections.append((heading.group(2), current))
        elif current is not None and line.strip() != "---":
            current.append(line)

    result: list[tuple[str, str]] = []
    for heading_text, lines in sections:
        text = "\n".join(lines).strip()
        if text:
            result.append((heading_text, text))
    return result


def split_text(text: str, max_chars: int) -> list[str]:
    """Pack whole paragraphs into chunks of at most max_chars.

    A paragraph is only divided if it is longer than max_chars on its own,
    and then it is divided between lines, then between words.
    """
    units: list[str] = []
    for paragraph in _PARAGRAPH_BREAK.split(text):
        if not paragraph.strip():
            continue
        if len(paragraph) <= max_chars:
            units.append(paragraph)
        else:
            units.extend(_divide(paragraph, max_chars))

    chunks: list[str] = []
    current = ""
    for unit in units:
        candidate = f"{current}\n\n{unit}" if current else unit
        if len(candidate) <= max_chars:
            current = candidate
        else:
            chunks.append(current)
            current = unit
    if current:
        chunks.append(current)
    return chunks


def _divide(paragraph: str, max_chars: int) -> list[str]:
    """Only reached for one paragraph longer than the limit."""
    pieces: list[str] = []
    current = ""
    for line in paragraph.split("\n"):
        for piece in _wrap_line(line, max_chars):
            candidate = f"{current}\n{piece}" if current else piece
            if len(candidate) <= max_chars:
                current = candidate
            else:
                pieces.append(current)
                current = piece
    if current:
        pieces.append(current)
    return pieces


def _wrap_line(line: str, max_chars: int) -> list[str]:
    if len(line) <= max_chars:
        return [line]
    wrapped: list[str] = []
    current = ""
    for word in line.split(" "):
        candidate = f"{current} {word}" if current else word
        if len(candidate) <= max_chars:
            current = candidate
        else:
            wrapped.append(current)
            current = word
    if current:
        wrapped.append(current)
    return wrapped
