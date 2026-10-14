"""What the assistant says when the corpus cannot support an answer (F3, D5).

Fixed text plus the corpus's own directory: each current policy and the team
that owns it, read from the documents' front matter. Nothing is guessed per
question -- naming the owner of the nearest weak match would be the software
deciding where a question belongs on evidence it has just called insufficient.

No model call. A refusal is decided in code and written from a file.
"""

from __future__ import annotations

from app.core.config import settings
from app.ingest.corpus import Document

REFUSAL_VERSION = "refusal-v1"


def refusal(documents: list[Document]) -> str:
    template = (settings.prompts_dir / f"{REFUSAL_VERSION}.md").read_text(encoding="utf-8")
    directory = "\n".join(
        f"- {d.title} (v{d.version}) — {d.owner}"
        for d in sorted(documents, key=lambda d: d.title)
        if d.status == "current"
    )
    return template.replace("{directory}", directory).strip()
