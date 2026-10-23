from __future__ import annotations

import re
from dataclasses import dataclass

_FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
_HEADING = re.compile(r"^(#{2,6})\s+(.+?)\s*#*\s*$")


@dataclass(frozen=True)
class Section:
    heading: str
    text: str


@dataclass(frozen=True)
class PolicyDocument:
    metadata: dict[str, str]
    sections: list[Section]


def parse_document(markdown: str) -> PolicyDocument:
    match = _FRONT_MATTER.match(markdown)
    if match is None:
        raise ValueError("Policy document must start with YAML front matter")

    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if not separator:
            continue
        metadata[key.strip()] = value.strip().strip("\"'")

    required = {"id", "title", "version", "effective", "owner", "status"}
    missing = required - metadata.keys()
    if missing:
        fields = ", ".join(sorted(missing))
        raise ValueError(f"Policy document is missing front matter fields: {fields}")

    sections: list[Section] = []
    heading: str | None = None
    content: list[str] = []

    def finish_section() -> None:
        if heading is not None:
            text = "\n".join(content).strip()
            if text:
                sections.append(Section(heading=heading, text=text))

    body = markdown[match.end():]
    for line in body.splitlines():
        found = _HEADING.match(line)
        if found:
            finish_section()
            heading = found.group(2).strip()
            content = []
        elif heading is not None:
            content.append(line)
    finish_section()

    if not sections:
        raise ValueError(f"Policy document {metadata['id']} has no non-empty sections")
    return PolicyDocument(metadata=metadata, sections=sections)
