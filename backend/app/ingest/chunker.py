"""Splitting a section into passages.

D1: one passage per section. A section only splits when it exceeds
CHUNK_MAX_TOKENS, and then only at sentence ends -- never mid-sentence
(REQ-I2). No section in the current corpus is anywhere near the cap.
"""

from __future__ import annotations

import re

# Plan P2: characters / 4 is close enough for a safety cap, and avoids adding
# a tokenizer dependency to count something that never binds.
_CHARS_PER_TOKEN = 4

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def approx_tokens(text: str) -> int:
    return -(-len(text) // _CHARS_PER_TOKEN)


def split(text: str, max_tokens: int, overlap_tokens: int) -> list[str]:
    """The section as one piece if it fits, otherwise whole sentences per piece.

    A single sentence longer than the cap is kept whole: cutting it would put
    half a clause in each passage, which is worse than one long passage.
    """
    if approx_tokens(text) <= max_tokens:
        return [text]

    pieces: list[str] = []
    current: list[str] = []
    for sentence in _SENTENCE_END.split(text):
        if current and approx_tokens(" ".join([*current, sentence])) > max_tokens:
            pieces.append(" ".join(current))
            current = _overlap(current, overlap_tokens)
        current.append(sentence)
    if current:
        pieces.append(" ".join(current))
    return pieces


def _overlap(sentences: list[str], overlap_tokens: int) -> list[str]:
    """The trailing whole sentences that fit within the overlap."""
    carried: list[str] = []
    for sentence in reversed(sentences):
        if approx_tokens(" ".join([sentence, *carried])) > overlap_tokens:
            break
        carried.insert(0, sentence)
    return carried
