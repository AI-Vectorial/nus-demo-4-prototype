"""Reading the policy documents from backend/corpus/.

A policy document is a Markdown file with front matter. Files without front
matter (EVALUATION.md, FICTION-AUDIT.md) are not policies and are skipped.
A policy with missing front matter is an error, not a silent skip.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

REQUIRED_FIELDS = ("id", "title", "version", "effective", "owner", "status")

_FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.S)


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    version: str
    effective: str
    owner: str
    status: str
    body: str
    path: Path


def read_documents(directory: Path) -> list[Document]:
    documents: list[Document] = []
    for path in sorted(Path(directory).glob("*.md")):
        match = _FRONT_MATTER.match(path.read_text(encoding="utf-8"))
        if not match:
            continue

        fields = _parse_fields(match.group(1))
        if "id" not in fields and "status" not in fields:
            continue

        missing = [name for name in REQUIRED_FIELDS if not fields.get(name)]
        if missing:
            raise ValueError(f"{path.name} is missing front matter: {', '.join(missing)}")

        documents.append(
            Document(
                id=fields["id"],
                title=fields["title"],
                version=fields["version"],
                effective=fields["effective"],
                owner=fields["owner"],
                status=fields["status"],
                body=match.group(2),
                path=path,
            )
        )
    return documents


def _parse_fields(block: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip('"')
    return fields
