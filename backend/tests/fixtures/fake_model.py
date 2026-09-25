"""A model that does not call the network -- and can fail on demand.

Failing on demand is the point. REQ-G6 says that when the provider is
unreachable the product returns retrieved passages with no composed answer,
and that behaviour is otherwise untestable without unplugging the internet.
A degraded mode nobody can test is a degraded mode nobody has tested.
"""

from __future__ import annotations

from app.generate import ProviderError

# Dropped before hashing. Without this, sentences that share nothing but
# grammar outscore sentences that share their subject.
_STOPWORDS = frozenset(
    """a an and are as at be been before but by can do does for from had has have
    how i if in into is it its more must no not of on or our shall should so than
    that the their them then there these they this to under up was we were what
    when where which who will with would you your""".split()
)


class FakeModel:
    """Canned responses, recorded calls, and optional failure.

        model = FakeModel(answer="Claims of 75 or more need approval.")
        model = FakeModel(fail=True)          # every call raises ProviderError
        model = FakeModel(fail_after=2)       # works twice, then fails
    """

    def __init__(
        self,
        *,
        answer: str = "A composed answer, from the passages provided.",
        embedding_dimensions: int = 1536,
        fail: bool = False,
        fail_after: int | None = None,
    ) -> None:
        self.answer = answer
        self.embedding_dimensions = embedding_dimensions
        self.fail = fail
        self.fail_after = fail_after

        self.generate_calls: list[dict] = []
        self.embed_calls: list[list[str]] = []

    def _maybe_fail(self, what: str) -> None:
        if self.fail:
            raise ProviderError(f"{what} failed (fake)", retryable=True)
        if self.fail_after is not None:
            total = len(self.generate_calls) + len(self.embed_calls)
            if total > self.fail_after:
                raise ProviderError(f"{what} failed after {self.fail_after} (fake)",
                                    retryable=True)

    def generate(self, prompt: str, *, system: str | None = None,
                 temperature: float = 0.0) -> str:
        self.generate_calls.append(
            {"prompt": prompt, "system": system, "temperature": temperature}
        )
        self._maybe_fail("generate")
        return self.answer

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.embed_calls.append(list(texts))
        self._maybe_fail("embed")
        # Deterministic, and different texts get different vectors -- so a test
        # asserting that the right passage came back is actually asserting it.
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        """A bag of words, hashed into the vector space.

        Word-based, not character-based. A character histogram gives almost no
        semantic signal -- two sentences about completely different things score
        nearly the same, because English letter frequencies are similar. A test
        built on that would report retrieval as broken when it is working, and
        send a team to debug code that is correct.

        Stopwords are dropped, because without that they dominate: two
        sentences sharing only "for", "is" and "the" scored higher than two
        sharing the word "approval". Real embedding models effectively
        downweight common words; this is the crude equivalent.
        """
        import re

        vector = [0.0] * self.embedding_dimensions
        words = [
            w for w in re.findall(r"[a-z0-9]+", text.lower())
            if w not in _STOPWORDS
        ]
        for word in words:
            # Stable across runs, unlike hash() which is salted per process.
            slot = sum(ord(c) * (i + 1) for i, c in enumerate(word))
            vector[slot % self.embedding_dimensions] += 1.0
        return vector

    @property
    def was_called(self) -> bool:
        """Did anything reach the model? The assertion a refusal test needs."""
        return bool(self.generate_calls)
