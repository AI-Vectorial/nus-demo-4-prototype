"""REQ-R5 and REQ-R6 on the real corpus, against the live index.

Marked live: it needs the indexed collection and the embedding provider, which
CI does not have. Run it with `pytest -m live`.
"""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.generate import embed
from app.retrieve import get_vector_store
from app.retrieve.retrieve import Grounded, Insufficient, retrieve
from tests.eval.evaluation import QUESTIONS, in_top_three, live_search, ranks

pytestmark = pytest.mark.live

ANSWERABLE = [q for q in QUESTIONS if q.answerable]
OUT_OF_SCOPE = [q for q in QUESTIONS if not q.answerable]


@pytest.mark.parametrize("question", ANSWERABLE, ids=lambda q: f"Q{q.number}")
def test_the_expected_section_is_in_the_top_three(question):
    hits = live_search(question)

    assert in_top_three(question, hits), (
        f"expected ranks {ranks(question, hits)}; got "
        f"{[(h.document_id, h.section, round(h.score, 3)) for h in hits[:3]]}"
    )


def _retrieve(question):
    return retrieve(question.text, store=get_vector_store(), embed=embed,
                    top_k=settings.retrieve_top_k, min_score=settings.min_score)


@pytest.mark.parametrize("question", ANSWERABLE, ids=lambda q: f"Q{q.number}")
def test_an_answerable_question_is_grounded_at_the_threshold(question):
    assert isinstance(_retrieve(question), Grounded)


@pytest.mark.parametrize("question", OUT_OF_SCOPE, ids=lambda q: f"Q{q.number}")
def test_an_out_of_scope_question_is_insufficient_at_the_threshold(question):
    result = _retrieve(question)

    assert isinstance(result, Insufficient), (
        f"top score {result.hits[0].score:.3f} >= MIN_SCORE {settings.min_score}: "
        f"{result.hits[0].document_id} {result.hits[0].section}"
    )
