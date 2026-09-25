"""GET /corpus and /corpus/{id} -- what lets someone check a citation.

The documents are read from disk on every request (REQ-B5). Copying them into
Postgres would give two sources of truth and a bug waiting to happen: the
corpus is five files of a few hundred lines, and the filesystem is already the
thing ingestion indexes.

The front-matter-and-headings parser below is deliberately a local copy rather
than an import from app.ingest. These two readers answer different questions --
ingestion chunks for embedding, browsing splits for reading -- and coupling
them means a change to chunking silently changes what the corpus browser
shows.
"""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from app.api.schemas import CorpusDocumentDetailOut, CorpusDocumentOut, CorpusSectionOut
from app.core.config import settings

router = APIRouter(tags=["corpus"])

# backend/, so a relative CORPUS_DIR means the same thing whatever the working
# directory of the process happens to be.
_ROOT = Path(__file__).resolve().parents[2]

_FRONT_MATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
_HEADING = re.compile(r"\A#{2,}\s+(.+?)\s*\Z")


def _parse(path: Path) -> tuple[dict[str, str], list[CorpusSectionOut]]:
    """Front matter, then everything under each heading below the title."""
    raw = path.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    body = raw
    header = _FRONT_MATTER.match(raw)
    if header:
        for line in header.group(1).splitlines():
            key, separator, value = line.partition(":")
            if separator:
                meta[key.strip()] = value.strip().strip('"')
        body = raw[header.end() :]
    sections: list[tuple[str, list[str]]] = []
    for line in body.splitlines():
        heading = _HEADING.match(line)
        if heading:
            sections.append((heading.group(1), []))
        elif sections:
            sections[-1][1].append(line)
    return meta, [
        CorpusSectionOut(heading=heading, text="\n".join(lines).strip())
        for heading, lines in sections
    ]


def _documents() -> list[tuple[dict[str, str], list[CorpusSectionOut]]]:
    directory = Path(settings.corpus_dir)
    if not directory.is_absolute():
        directory = _ROOT / directory
    parsed = [_parse(path) for path in sorted(directory.glob("*.md"))]
    # MANIFEST.yaml and EVALUATION.md live here too; a policy document is one
    # with an id in its front matter.
    return [(meta, sections) for meta, sections in parsed if meta.get("id")]


@router.get("/corpus", response_model=list[CorpusDocumentOut])
def list_corpus() -> list[CorpusDocumentOut]:
    """Every document, with its section headings -- REQ-B1.

    Superseded documents are listed alongside current ones and carry their
    status (D4). Hiding one would make "has this changed?" unanswerable.
    """
    return [
        CorpusDocumentOut(
            id=meta.get("id", ""),
            title=meta.get("title", ""),
            owner=meta.get("owner", ""),
            version=meta.get("version", ""),
            effective=meta.get("effective", ""),
            status=meta.get("status", "current"),
            sections=[section.heading for section in sections],
        )
        for meta, sections in _documents()
    ]


@router.get("/corpus/{document_id}", response_model=CorpusDocumentDetailOut)
def get_corpus_document(
    document_id: str,
    version: str | None = Query(default=None, description="Defaults to the current version"),
) -> CorpusDocumentDetailOut:
    """One document and the text of its sections -- REQ-B3.

    travel-expense-policy exists twice, 3.1 current and 3.0 superseded, under
    one id. Without ?version the current one is served, so a citation link
    lands on the policy in force.
    """
    candidates = [
        (meta, sections) for meta, sections in _documents() if meta.get("id") == document_id
    ]
    if not candidates:
        raise HTTPException(status_code=404, detail="document not found")

    if version is not None:
        candidates = [(meta, s) for meta, s in candidates if meta.get("version") == version]
        if not candidates:
            raise HTTPException(status_code=404, detail="version not found")
    elif len(candidates) > 1:
        current = [(meta, s) for meta, s in candidates if meta.get("status") == "current"]
        candidates = current or sorted(candidates, key=lambda pair: pair[0].get("version", ""))[-1:]

    meta, sections = candidates[0]
    return CorpusDocumentDetailOut(
        id=meta.get("id", ""),
        title=meta.get("title", ""),
        owner=meta.get("owner", ""),
        version=meta.get("version", ""),
        effective=meta.get("effective", ""),
        status=meta.get("status", "current"),
        sections=sections,
    )
