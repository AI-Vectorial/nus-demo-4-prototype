"""The prompt and the refusal, loaded from versioned files (REQ-G4).

Wording lives in app/generate/prompts/, never in Python, so a change to what
the model is told is a change to a file with a version -- and every answer
records which version produced it (REQ-G5).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.ingest import CORPUS_DIR
from app.ingest.loader import load_corpus
from app.retrieve.store import Hit

PROMPTS = Path(__file__).resolve().parent / "prompts"

_FRONT_MATTER = re.compile(r"^---\nversion: (\S+)\n---\n", re.S)


@dataclass(frozen=True)
class Prompt:
    path: Path
    version: str
    system: str
    user: str

    def render(self, question: str, hits: list[Hit]) -> str:
        return (self.user
                .replace("{{passages}}", "\n\n".join(_passage(n, h) for n, h in
                                                      enumerate(hits, start=1)))
                .replace("{{question}}", question))


def _read(name: str) -> tuple[Path, str, str]:
    path = PROMPTS / name
    text = path.read_text(encoding="utf-8")
    match = _FRONT_MATTER.match(text)
    if not match:
        raise ValueError(f"{path.name} does not declare a version")
    return path, match.group(1), text[match.end():].strip()


def _passage(number: int, hit: Hit) -> str:
    """One passage, labelled with where it is from and whether it is current (D4)."""
    version = hit.metadata.get("version", "")
    status = hit.metadata.get("status", "")
    return (f"[{number}] {hit.document_title} v{version} ({status}) — {hit.section}\n"
            f"{hit.text}")


@lru_cache(maxsize=1)
def load_prompt() -> Prompt:
    path, version, body = _read("answer.md")
    system, _, user = body.partition("## User")
    return Prompt(
        path=path,
        version=version,
        system=system.removeprefix("## System").strip(),
        user=user.strip(),
    )


@lru_cache(maxsize=1)
def refusal_text() -> str:
    """D5: not covered, what is covered and by whom, and Compliance for the rest.

    The list comes from the corpus itself, so it cannot drift from what is
    indexed. Superseded versions are not somewhere to send anyone.
    """
    _, _, body = _read("refusal.md")
    areas = "\n".join(
        f"- {doc.title} — {doc.owner}"
        for doc in load_corpus(CORPUS_DIR)
        if doc.status == "current"
    )
    return body.replace("{{areas}}", areas)
