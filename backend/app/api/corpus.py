from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.ingest.parser import parse_document

router = APIRouter(tags=["corpus"])
CORPUS_DIR = Path(__file__).resolve().parents[2] / "corpus"
_MANIFEST_DOCUMENT = re.compile(
    r"(?m)^  - id:\s*(?P<id>[^\n]+)\n(?P<fields>(?:^    [^\n]*\n?)*)"
)
_FRONT_MATTER = re.compile(r"\A---\s*\n.*?\n---\s*(?:\n|\Z)", re.DOTALL)


class CorpusDocument(BaseModel):
    id: str
    title: str
    version: str
    effective: str
    owner: str
    status: Literal["current", "superseded"]


class CorpusDocumentDetail(CorpusDocument):
    content: str


def _documents() -> list[tuple[CorpusDocument, Path]]:
    manifest_path = CORPUS_DIR / "MANIFEST.yaml"
    manifest = manifest_path.read_text(encoding="utf-8")
    if "documents:" not in manifest:
        raise RuntimeError("Corpus manifest does not define documents")

    document_section = manifest.split("documents:", maxsplit=1)[1].split(
        "\n# ---------------------------------------------------------------------------",
        maxsplit=1,
    )[0]
    records: list[tuple[CorpusDocument, Path]] = []
    for match in _MANIFEST_DOCUMENT.finditer(document_section):
        values = {"id": match.group("id").strip().strip("\"'")}
        for line in match.group("fields").splitlines():
            key, separator, value = line.strip().partition(":")
            if separator:
                values[key] = value.strip().strip("\"'")
        filename = values.get("file", "")
        if not filename or Path(filename).name != filename:
            raise RuntimeError("Corpus manifest contains an invalid document filename")

        path = CORPUS_DIR / filename
        parsed = parse_document(path.read_text(encoding="utf-8"))
        metadata = parsed.metadata
        records.append(
            (
                CorpusDocument(
                    id=values["id"],
                    title=metadata["title"],
                    version=metadata["version"],
                    effective=metadata["effective"],
                    owner=metadata["owner"],
                    status=metadata["status"],
                ),
                path,
            )
        )
    if not records:
        raise RuntimeError("Corpus manifest contains no documents")
    return records


@router.get("/corpus", response_model=dict[str, list[CorpusDocument]])
def list_corpus() -> dict[str, list[CorpusDocument]]:
    return {"documents": [document for document, _ in _documents()]}


@router.get("/corpus/{document_id}", response_model=CorpusDocumentDetail)
def get_corpus_document(
    document_id: str, version: str | None = None
) -> CorpusDocumentDetail:
    candidates = [
        (document, path)
        for document, path in _documents()
        if document.id == document_id and (version is None or document.version == version)
    ]
    if version is None:
        candidates = [
            candidate for candidate in candidates if candidate[0].status == "current"
        ]
    if not candidates:
        raise HTTPException(status_code=404, detail="Policy document not found")
    if len(candidates) > 1:
        raise HTTPException(status_code=409, detail="Policy document version is ambiguous")

    document, path = candidates[0]
    markdown = path.read_text(encoding="utf-8")
    front_matter = _FRONT_MATTER.match(markdown)
    if front_matter is None:
        raise RuntimeError(f"Policy document {document.id} has invalid front matter")
    return CorpusDocumentDetail(
        **document.model_dump(),
        content=markdown[front_matter.end() :].strip(),
    )
