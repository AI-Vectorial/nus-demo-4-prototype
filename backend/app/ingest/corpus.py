"""Reading the policy corpus from disk.

The documents in backend/corpus/ are the source of truth for ingestion, for the
corpus browser and for the refusal's directory of policy owners (REQ-B5), so
they are parsed in one place and nothing else reads the Markdown directly.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_HEADING = re.compile(r"^(#{1,3}) +(.+?)\s*$")
_RULE = re.compile(r"^-{3,}\s*$")


@dataclass(frozen=True)
class Section:
    heading: str
    text: str


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    version: str
    effective: str
    owner: str
    status: str
    sections: tuple[Section, ...]


def _front_matter(raw: str) -> tuple[dict[str, str], str]:
    match = _FRONT_MATTER.match(raw)
    if not match:
        return {}, raw
    fields = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip().strip('"')
    return fields, raw[match.end():]


def _sections(body: str, title: str) -> list[Section]:
    """Split on headings. What precedes the first ## belongs to the title."""
    sections: list[Section] = []
    heading, lines = title, []
    for line in body.splitlines():
        match = _HEADING.match(line)
        if match and match.group(1) != "#":
            sections.append(Section(heading, "\n".join(lines).strip()))
            heading, lines = match.group(2), []
        elif not match and not _RULE.match(line):
            lines.append(line)
    sections.append(Section(heading, "\n".join(lines).strip()))
    return sections


def parse(path: Path) -> Document:
    fields, body = _front_matter(path.read_text(encoding="utf-8"))
    title = fields["title"]
    return Document(
        id=fields["id"],
        title=title,
        version=fields["version"],
        effective=fields["effective"],
        owner=fields["owner"],
        status=fields["status"],
        sections=tuple(_sections(body, title)),
    )


def load(corpus_dir: Path) -> list[Document]:
    """Every policy document, current and superseded (REQ-I7), in a stable order.

    A policy document is a Markdown file with front matter; EVALUATION.md and
    the audit notes have none and are not policy.
    """
    documents = []
    for path in sorted(corpus_dir.glob("*.md")):
        if _FRONT_MATTER.match(path.read_text(encoding="utf-8")):
            documents.append(parse(path))
    return documents
