"""The team's PRD section 10 values arrive from the environment, and only from there.

A value the team chose and defended at the plan gate must not be quietly
replaced by a number somebody typed into the code.
"""

from __future__ import annotations

import pytest

from app.core.config import ConfigurationError, Settings

DECISIONS = {
    "MIN_SCORE": ("min_score", "0.35", 0.35),
    "CHUNK_MAX_TOKENS": ("chunk_max_tokens", "400", 400),
    "CHUNK_OVERLAP_TOKENS": ("chunk_overlap_tokens", "60", 60),
    "RETRIEVE_TOP_K": ("retrieve_top_k", "6", 6),
}


@pytest.mark.parametrize("variable", DECISIONS)
def test_a_decision_is_read_from_the_environment(monkeypatch, variable):
    attribute, raw, expected = DECISIONS[variable]
    monkeypatch.setenv(variable, raw)

    assert getattr(Settings(), attribute) == expected


@pytest.mark.parametrize("variable", DECISIONS)
def test_an_unset_decision_has_no_default_and_says_which_variable(monkeypatch, variable):
    attribute, *_ = DECISIONS[variable]
    monkeypatch.delenv(variable, raising=False)

    with pytest.raises(ConfigurationError, match=variable):
        getattr(Settings(), attribute)


def test_an_unset_decision_does_not_stop_the_app_loading(monkeypatch):
    # /healthz must answer even when configuration is incomplete -- NFR-5.
    for variable in DECISIONS:
        monkeypatch.delenv(variable, raising=False)

    Settings()
