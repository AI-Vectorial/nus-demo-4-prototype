"""F2 retrieve and F3 refuse. Epic criteria 7 to 12.

Criterion 7 needs real embeddings, so it is evidenced by
`python -m app.retrieve.evaluate` against the live index -- recorded in
tickets/T1-F2-retrieve.md. What is tested here is the mechanism: the type,
the threshold, and that a refusal never reaches the model.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from app.core.config import settings
from app.retrieve import Grounded, Insufficient, retrieve
from app.retrieve.evaluate import CASES
from app.retrieve.store import Hit

APP = Path(__file__).resolve().parents[2] / "app"
BACKEND = APP.parent


class _IgnoresThreshold:
    """A store that returns everything, weak matches included."""

    def __init__(self, scores: list[float]) -> None:
        self.scores = scores

    def search(self, embedding, limit=5, min_score=0.0):
        return [Hit(passage_id=str(i), text="t", document_id="d", document_title="D",
                    section="1.1 S", score=s) for i, s in enumerate(self.scores)][:limit]


# --------------------------------------------------------------- criterion 7


def test_a_relevant_question_is_grounded_with_the_right_passage_first(loaded_store, model):
    """REQ-R1 -- the mechanism criterion 7 runs on."""
    result = retrieve("What is the approval threshold for expenses?", loaded_store,
                      model.embed, min_score=0.1)

    assert isinstance(result, Grounded)
    assert result.hits[0].document_id == "travel-expense-policy"


def test_retrieval_returns_at_most_top_k(loaded_store, model):
    result = retrieve("client correspondence approval refresh", loaded_store, model.embed,
                      top_k=2, min_score=0.0)
    assert isinstance(result, Grounded)
    assert len(result.hits) <= 2


def test_the_evaluation_set_is_complete():
    """Ten answerable, three that must refuse -- as corpus/EVALUATION.md has it."""
    assert [c.number for c in CASES] == list(range(1, 14))
    assert sum(1 for c in CASES if c.expected) == 10


# --------------------------------------------------------------- criterion 8


def test_nothing_below_the_threshold_is_returned():
    """REQ-R2 -- even when the store does not filter."""
    store = _IgnoresThreshold([0.9, 0.6, 0.51, 0.2])

    result = retrieve("q", store, lambda texts: [[1.0]], min_score=0.517)

    assert isinstance(result, Grounded)
    assert [h.score for h in result.hits] == [0.9, 0.6]


def test_a_score_exactly_at_the_threshold_is_kept():
    result = retrieve("q", _IgnoresThreshold([0.517]), lambda t: [[1.0]], min_score=0.517)
    assert isinstance(result, Grounded)


# --------------------------------------------------------------- criterion 9


def test_nothing_above_the_threshold_is_an_explicit_insufficiency():
    """REQ-R3, REQ-R6 -- a type, not an empty list."""
    result = retrieve("q", _IgnoresThreshold([0.501, 0.3]), lambda t: [[1.0]],
                      min_score=0.517)

    assert isinstance(result, Insufficient)
    assert not hasattr(result, "hits")


def test_grounded_cannot_be_built_empty():
    with pytest.raises(ValueError):
        Grounded(hits=[])


# --------------------------------------------------------------- criterion 10


def test_an_insufficient_retrieval_never_calls_the_model(loaded_store, model):
    """REQ-R3, NFR-2 -- embedding the question is the only model traffic."""
    before = len(model.embed_calls)  # the fixture embedded the passages already

    result = retrieve("something entirely unrelated to banking policy", loaded_store,
                      model.embed, min_score=0.99)

    assert isinstance(result, Insufficient)
    assert not model.was_called
    assert model.embed_calls[before:] == [["something entirely unrelated to banking policy"]]


# --------------------------------------------------------------- criterion 12


def test_the_threshold_defaults_to_configuration():
    """REQ-R4 -- what retrieve() uses when nobody passes one."""
    store = _IgnoresThreshold([settings.min_score])
    assert isinstance(retrieve("q", store, lambda t: [[1.0]]), Grounded)


def test_min_score_above_any_score_refuses_all_thirteen_with_no_code_change():
    """REQ-R4 -- set only the environment variable, in a fresh process."""
    script = (
        "from app.ingest import ingest\n"
        "from app.retrieve import Insufficient, retrieve\n"
        "from app.retrieve.evaluate import CASES\n"
        "from tests.fixtures.fake_model import FakeModel\n"
        "from tests.fixtures.fake_store import FakeVectorStore\n"
        "store, model = FakeVectorStore(), FakeModel()\n"
        "ingest(store, model.embed)\n"
        "results = [retrieve(c.question, store, model.embed) for c in CASES]\n"
        "assert all(isinstance(r, Insufficient) for r in results), results\n"
        "print(len(results))\n"
    )
    env = {**os.environ, "MIN_SCORE": "1.01"}
    done = subprocess.run(  # noqa: S603 - our own interpreter, our own script
        [sys.executable, "-c", script], cwd=BACKEND, env=env,
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == "13"


def test_no_threshold_literal_in_application_code():
    """REQ-R4 -- the number lives in configuration, nowhere else."""
    allowed = {"core/config.py"}
    pattern = re.compile(r"(min_score|score)\s*(>=|<=|>|<|==|=)\s*-?\d")
    offenders = [
        f"{path.relative_to(APP)}:{n}"
        for path in APP.rglob("*.py")
        if path.relative_to(APP).as_posix() not in allowed
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if pattern.search(line)
    ]
    assert not offenders
