"""Read the policy corpus and split it into sections.

A section begins at a heading (## or ###) and runs to the next heading. The
section heading is the citation name, so a passage is always a whole section and
never cut mid-sentence (REQ-I2).
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from app.retrieve.store import Passage

CORPUS_DIR = Path(__file__).resolve().parents[2] / "corpus"

_HEADING = re.compile(r"^(#{2,3}) (.+?)\s*$")
_FRONT_MATTER = re.compile(r"^---\n(.*?)\n---\n", re.S)
# Not policy documents: they have no front matter, but skip them by name too.
_NOT_POLICY = {"EVALUATION", "FICTION-AUDIT"}


def _front_matter(text: str) -> dict[str, str]:
    match = _FRONT_MATTER.match(text)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip().strip('"')
    return fields


def _sections(text: str) -> list[tuple[str, str]]:
    """(heading, full section text including its heading), in document order."""
    body = _FRONT_MATTER.sub("", text, count=1)
    sections: list[tuple[str, list[str]]] = []
    for line in body.splitlines():
        match = _HEADING.match(line)
        if match:
            sections.append((match.group(2), [line]))
        elif sections:
            sections[-1][1].append(line)
    return [(heading, "\n".join(lines).strip()) for heading, lines in sections]


def _passage_id(document_id: str, version: str, section: str, text: str) -> str:
    """A stable UUID: the same content always gets the same id (REQ-I4)."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{document_id}|{version}|{section}|{text}"))


def load_corpus(corpus_dir: Path = CORPUS_DIR) -> list[Passage]:
    """Every section of every policy document, with no embeddings yet."""
    passages: list[Passage] = []
    for path in sorted(corpus_dir.glob("*.md")):
        if path.stem in _NOT_POLICY:
            continue
        raw = path.read_text(encoding="utf-8")
        front = _front_matter(raw)
        if "id" not in front:
            continue
        for heading, text in _sections(raw):
            passages.append(
                Passage(
                    id=_passage_id(front["id"], front["version"], heading, text),
                    text=text,
                    document_id=front["id"],
                    document_title=front["title"],
                    section=heading,
                    embedding=[],
                    metadata={
                        "version": front["version"],
                        "status": front["status"],
                        "effective": front.get("effective", ""),
                    },
                )
            )
    return passages
