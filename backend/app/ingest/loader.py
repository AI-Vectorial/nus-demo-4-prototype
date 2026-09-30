"""Reading policy documents from disk.

A document is Markdown with flat front matter. Its sections are its `##` and
`###` headings; the `#` title and anything before the first section are not
policy text and are not indexed.

The front matter is flat `key: value` pairs, so it is parsed here rather than
by a YAML library -- one fewer dependency for a format with no nesting.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_FRONT_MATTER = re.compile(r"^---\n(.*?)\n---\n", re.S)
_HEADING = re.compile(r"^(#{1,3}) (.+)$")
_RULE = re.compile(r"^-{3,}$")

# Files in the corpus directory that are about the corpus, not policy.
_NOT_POLICY = {"EVALUATION", "FICTION-AUDIT"}


@dataclass(frozen=True)
class Section:
    """One heading and the text directly beneath it."""

    heading: str
    text: str
    parent: str | None = None


@dataclass(frozen=True)
class Document:
    """One policy document, one version of it."""

    id: str
    title: str
    version: str
    effective: str
    owner: str
    status: str
    sections: list[Section] = field(default_factory=list)


def _front_matter(text: str) -> tuple[dict[str, str], str]:
    match = _FRONT_MATTER.match(text)
    if not match:
        raise ValueError("document has no front matter")
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip().strip('"')
    return fields, text[match.end():]


def _sections(body: str) -> list[Section]:
    sections: list[Section] = []
    parent: str | None = None
    heading: str | None = None
    heading_parent: str | None = None
    lines: list[str] = []

    def close() -> None:
        text = "\n".join(lines).strip()
        if heading and text:
            sections.append(Section(heading=heading, text=text, parent=heading_parent))

    for line in body.splitlines():
        match = _HEADING.match(line)
        if not match:
            if not _RULE.match(line.strip()):
                lines.append(line)
            continue

        close()
        level, title = len(match.group(1)), match.group(2).strip()
        lines = []
        if level == 1:
            heading, heading_parent = None, None
        elif level == 2:
            parent = title
            heading, heading_parent = title, None
        else:
            heading, heading_parent = title, parent
    close()
    return sections


def parse_document(text: str) -> Document:
    fields, body = _front_matter(text)
    return Document(
        id=fields["id"],
        title=fields["title"],
        version=fields["version"],
        effective=fields["effective"],
        owner=fields["owner"],
        status=fields["status"],
        sections=_sections(body),
    )


def load_corpus(directory: Path) -> list[Document]:
    """Every policy document in the directory, in a stable order."""
    return [
        parse_document(path.read_text(encoding="utf-8"))
        for path in sorted(directory.glob("*.md"))
        if path.stem not in _NOT_POLICY
    ]
