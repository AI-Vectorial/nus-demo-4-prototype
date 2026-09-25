"""Reading the policy corpus off disk, and refusing to index one that has drifted.

MANIFEST.yaml is the authority on what the corpus contains. Everything here
exists to make a mismatch between the manifest and the files a loud failure at
ingest time rather than a quiet one at query time -- an unlisted document that
gets indexed, or a version in the front matter that no longer matches the
version a citation will claim, is the kind of wrong that still looks right.

Every failure names the file, because "validation failed" sends someone
reading five documents to find out which one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings

# backend/ -- CORPUS_DIR is written relative to it, as the service runs there.
BACKEND = Path(__file__).resolve().parents[2]

MANIFEST = "MANIFEST.yaml"

# Front matter: the leading --- block. A .md file without one is not a policy
# document (corpus/EVALUATION.md is the reason that distinction is needed).
_FRONT_MATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)

# Sections are ## and ### only. The single # is the document title, which the
# front matter already carries.
_HEADING = re.compile(r"^#{2,3}[ \t]+(.+?)[ \t]*$", re.MULTILINE)

# What a citation promises, so all of it must be present and must agree with
# the manifest.
_REQUIRED_FIELDS = ("id", "title", "version", "effective", "status", "owner")

# Fields the manifest and the document must agree on. `title` is excluded on
# purpose: the manifest holds the canonical wording and a document is free to
# render it differently.
_MUST_MATCH = ("id", "version", "status")


class CorpusError(RuntimeError):
    """The corpus does not match its manifest. The message always names a file."""


@dataclass(frozen=True)
class Section:
    """One numbered section of one policy document."""

    heading: str
    text: str


@dataclass(frozen=True)
class Document:
    """One policy document, with everything a citation needs."""

    file: str
    id: str
    title: str
    version: str
    effective: str
    status: str
    owner: str
    sections: list[Section]


def corpus_path() -> Path:
    """Where the documents live. Relative paths resolve against backend/."""
    configured = Path(settings.corpus_dir)
    return configured if configured.is_absolute() else BACKEND / configured


def load_corpus(directory: Path | None = None) -> list[Document]:
    """Every policy document, in manifest order, validated against the manifest.

    Raises CorpusError -- naming the file -- if a listed document is missing, a
    present document is unlisted, or a document's front matter contradicts what
    the manifest says about it.
    """
    root = directory or corpus_path()
    manifest_file = root / MANIFEST
    if not manifest_file.exists():
        raise CorpusError(f"{MANIFEST}: not found in {root}")

    listed = _manifest_documents(manifest_file.read_text(encoding="utf-8"))
    if not listed:
        raise CorpusError(f"{MANIFEST}: lists no documents")

    _reject_unlisted(root, {entry.get("file", "") for entry in listed})

    return [_load_document(root, entry) for entry in listed]


def _reject_unlisted(root: Path, listed_files: set[str]) -> None:
    """A document nobody declared is a document nobody reviewed."""
    for path in sorted(root.glob("*.md")):
        if not _FRONT_MATTER.match(path.read_text(encoding="utf-8")):
            continue  # not a policy document -- EVALUATION.md, for instance
        if path.name not in listed_files:
            raise CorpusError(
                f"{path.name}: present in the corpus but not listed in {MANIFEST}"
            )


def _load_document(root: Path, entry: dict[str, str]) -> Document:
    name = entry.get("file", "")
    if not name:
        raise CorpusError(f"{MANIFEST}: a document entry has no `file`")

    path = root / name
    if not path.exists():
        raise CorpusError(f"{name}: listed in {MANIFEST} but not present in {root}")

    raw = path.read_text(encoding="utf-8")
    match = _FRONT_MATTER.match(raw)
    if not match:
        raise CorpusError(
            f"{name}: no YAML front matter -- a policy document must declare "
            "its id, version and status"
        )

    fields = _mapping(match.group(1))
    missing = [key for key in _REQUIRED_FIELDS if not fields.get(key)]
    if missing:
        raise CorpusError(f"{name}: front matter is missing {', '.join(missing)}")

    for key in _MUST_MATCH:
        if key in entry and fields[key] != entry[key]:
            raise CorpusError(
                f"{name}: front matter {key} is {fields[key]!r} but {MANIFEST} "
                f"says {entry[key]!r}"
            )

    sections = _sections(raw[match.end() :])
    if not sections:
        raise CorpusError(f"{name}: no ## or ### sections -- nothing to index")

    return Document(
        file=name,
        id=fields["id"],
        title=fields["title"],
        version=fields["version"],
        effective=fields["effective"],
        status=fields["status"],
        owner=fields["owner"],
        sections=sections,
    )


def _sections(body: str) -> list[Section]:
    """Split on ## and ### boundaries (REQ-I2), heading text kept verbatim."""
    headings = list(_HEADING.finditer(body))
    sections: list[Section] = []
    for index, match in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(body)
        sections.append(Section(heading=match.group(1), text=body[match.end() : end].strip()))
    return sections


# --- The smallest possible YAML ------------------------------------------
# Hand-rolled rather than pyyaml: adding a dependency is a decision for the
# team (AGENTS.md section 5), and what has to be read here is a flat mapping
# and a list of flat mappings. Anything richer in MANIFEST.yaml -- the block
# scalars under known_conflict, say -- is deliberately ignored.


def _scalar(raw: str) -> str:
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _mapping(block: str) -> dict[str, str]:
    """`key: value` pairs from one flat block, such as a front matter header."""
    fields: dict[str, str] = {}
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        fields[key.strip()] = _scalar(value)
    return fields


def _manifest_documents(text: str) -> list[dict[str, str]]:
    """The top-level `documents:` list. Other top-level keys end it."""
    documents: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    inside = False

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line[:1].isspace():
            # A key at column zero: either the list we want, or the end of it.
            inside = stripped.partition(":")[0] == "documents"
            current = None
            continue
        if not inside:
            continue
        if stripped.startswith("- "):
            current = {}
            documents.append(current)
            stripped = stripped[2:]
        if current is None or ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        current[key.strip()] = _scalar(value)

    return documents
