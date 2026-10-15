"""F4 -- generate. REQ-G1 to REQ-G5. The prompt is a versioned file, not a literal.

compose_answer() is called only with passages retrieval has grounded. It sends
the passages and the recent questions to the model, and returns the text.

It raises ProviderError when the model is unreachable. The caller turns that
into a degraded response (REQ-G6). It is not caught here.
"""

from __future__ import annotations

from pathlib import Path

from app.generate.client import ProviderError, generate
from app.retrieve.store import Hit

PROMPT_VERSION = "answer-v1"
_PROMPT_FILE = Path(__file__).parent / "prompts" / f"{PROMPT_VERSION}.md"


def system_prompt() -> str:
    return _PROMPT_FILE.read_text(encoding="utf-8").strip()


def _passage_block(index: int, hit: Hit) -> str:
    status = hit.metadata.get("status", "current")
    version = hit.metadata.get("version", "?")
    flag = " SUPERSEDED" if status == "superseded" else ""
    return (
        f"[{index}] {hit.document_title} — {hit.section} "
        f"(version {version},{flag} {status})\n{hit.text}"
    )


def build_user_message(question: str, passages: list[Hit], earlier: list[str]) -> str:
    parts: list[str] = []
    if earlier:
        parts.append(
            "Earlier questions in this conversation, for context only. "
            "The answer is to the question at the end:\n"
            + "\n".join(f"- {q}" for q in earlier)
        )
    parts.append(
        "Policy passages (the only source you may use):\n\n"
        + "\n\n".join(_passage_block(i, h) for i, h in enumerate(passages, start=1))
    )
    parts.append(f"Question: {question}")
    return "\n\n".join(parts)


def compose_answer(question: str, passages: list[Hit], earlier: list[str]) -> str:
    text = generate(
        build_user_message(question, passages, earlier),
        system=system_prompt(),
        temperature=0.0,
    )
    if not text:
        # An empty reply is a failed answer, not an answer (review F2).
        raise ProviderError("the model returned an empty answer", retryable=True)
    return text
