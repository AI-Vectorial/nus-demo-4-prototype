from __future__ import annotations

import re

import tiktoken

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _token_count(text: str, encoding: tiktoken.Encoding) -> int:
    return len(encoding.encode(text))


def chunk_section(
    text: str,
    max_tokens: int,
    overlap_tokens: int,
    *,
    model: str,
) -> list[str]:
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    if overlap_tokens < 0 or overlap_tokens >= max_tokens:
        raise ValueError("overlap_tokens must be non-negative and smaller than max_tokens")

    encoding = tiktoken.encoding_for_model(model.rsplit("/", maxsplit=1)[-1])
    sentences = [
        sentence.strip()
        for sentence in _SENTENCE_END.split(text.strip())
        if sentence.strip()
    ]
    chunks: list[str] = []
    current: list[str] = []

    for sentence in sentences:
        if _token_count(sentence, encoding) > max_tokens:
            raise ValueError("A sentence exceeds CHUNK_MAX_TOKENS and cannot be split safely")
        if current and _token_count(" ".join([*current, sentence]), encoding) > max_tokens:
            chunks.append(" ".join(current))
            overlap: list[str] = []
            if overlap_tokens:
                overlap_count = 0
                for previous in reversed(current):
                    overlap.insert(0, previous)
                    overlap_count += _token_count(previous, encoding)
                    if overlap_count >= overlap_tokens:
                        break
                while overlap and (
                    _token_count(" ".join([*overlap, sentence]), encoding) > max_tokens
                ):
                    overlap.pop(0)
            current = overlap
        current.append(sentence)

    if current:
        chunks.append(" ".join(current))
    return chunks
