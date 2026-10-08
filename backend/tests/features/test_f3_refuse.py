"""F3 -- refuse. Criteria C5, C6, C7 in tickets/T1.md (D5).

C5 itself -- Q11 to Q13 refused on the real index -- depends on MIN_SCORE (D2),
which is not yet signed off. C7 -- a refusal never calls the model -- is tested
where the decision is made, in test_f5_ask.py. These hold what does not depend
on either.
"""

from __future__ import annotations

from pathlib import Path

from app.features.refuse import REFUSAL_VERSION, refusal
from app.ingest import corpus

CORPUS = Path(__file__).resolve().parents[2] / "corpus"


def test_c6_a_refusal_says_the_policies_do_not_support_the_question():
    text = refusal(corpus.load(CORPUS))

    assert "do not support an answer" in text


def test_c6_a_refusal_lists_every_current_policy_and_its_owner_from_the_corpus():
    documents = corpus.load(CORPUS)
    text = refusal(documents)

    for d in documents:
        if d.status == "current":
            assert d.title in text
            assert d.owner in text


def test_d5_the_superseded_version_is_not_offered_as_somewhere_to_go():
    text = refusal(corpus.load(CORPUS))

    assert "3.0" not in text
    assert text.count("Travel and Expense Policy") == 1


def test_d5_a_refusal_invents_no_contact_route():
    text = refusal(corpus.load(CORPUS)).lower()

    for invented in ("@", "http", "email", "phone", "extension", "hr "):
        assert invented not in text


def test_the_refusal_text_is_versioned():
    assert REFUSAL_VERSION == "refusal-v1"
