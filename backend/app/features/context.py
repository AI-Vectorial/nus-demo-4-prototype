"""What a follow-up sees (D8) and what it retrieves on (D9).

One window serves both: the last CONTEXT_MESSAGES messages -- rows, not turns --
counting the question being asked. The answer is composed with the whole window;
retrieval runs on the user questions inside it and never on the assistant's
answers, which would drag every search back towards the passages already found.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Turn:
    role: str  # user | assistant
    content: str


def window(history: list[Turn], question: str, *, size: int) -> list[Turn]:
    """The last `size` messages, the current question included."""
    return [*history, Turn("user", question)][-size:]


def retrieval_questions(turns: list[Turn]) -> list[str]:
    return [t.content for t in turns if t.role == "user"]
