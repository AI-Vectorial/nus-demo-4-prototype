"""Review F12: one time budget per answer, so a slow model cannot outlive the gateway.

The live failure was a 504 from the gateway. Two real answers took 89 s and
108 s, because retries and per-call timeouts multiplied with no overall limit.
These tests drive a fake clock, so they run instantly.
"""

from __future__ import annotations

from dataclasses import replace

import httpx
import pytest
from openai import APITimeoutError

from app.core.config import settings
from app.generate import client
from app.generate.client import ProviderError, _call, time_budget


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock(monkeypatch) -> FakeClock:
    fake = FakeClock()
    monkeypatch.setattr(client, "_now", fake)
    monkeypatch.setattr(client, "_sleep", lambda seconds: setattr(fake, "now", fake.now + seconds))
    return fake


def _timeout_error() -> APITimeoutError:
    return APITimeoutError(request=httpx.Request("POST", "http://test.invalid"))


def test_retries_stop_when_the_budget_is_spent(clock):
    calls = []

    def slow_failure():
        calls.append(1)
        clock.now += 4  # each attempt takes 4 seconds, then times out
        raise _timeout_error()

    with time_budget(10), pytest.raises(ProviderError) as raised:
        _call(slow_failure, what="generate", attempts=3)

    # Attempt 1 ends at 4s, a 1s pause, attempt 2 ends at 9s, a 1s pause to 10s.
    # Then the budget is spent, so there is no third attempt.
    assert len(calls) == 2
    assert clock.now == pytest.approx(10)
    assert raised.value.retryable is True


def test_no_call_is_made_once_the_budget_is_spent(clock):
    calls = []

    with time_budget(0), pytest.raises(ProviderError):
        _call(lambda: calls.append(1), what="embed", attempts=3)

    assert calls == []


def test_a_backoff_never_sleeps_past_the_budget(clock):
    def rate_limited():
        from openai import RateLimitError

        clock.now += 1
        raise RateLimitError(
            "limited", response=httpx.Response(429, request=httpx.Request("POST", "http://t")),
            body=None,
        )

    with time_budget(3), pytest.raises(ProviderError):
        _call(rate_limited, what="generate", attempts=3)

    assert clock.now <= 3 + 1  # the last call can run past the budget by one call, no more


def test_the_sdk_timeout_is_capped_by_what_is_left_of_the_budget(monkeypatch, clock):
    seen: dict = {}

    class FakeOpenAI:
        def __init__(self, **kwargs):
            seen.update(kwargs)

    monkeypatch.setattr(client, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(
        client,
        "settings",
        replace(settings, openrouter_api_key="test-key", llm_timeout_seconds=60),
    )

    with time_budget(7):
        client._client()  # noqa: SLF001

    assert seen["timeout"] == pytest.approx(7)


def test_without_a_budget_the_configured_timeout_is_used(monkeypatch):
    seen: dict = {}

    class FakeOpenAI:
        def __init__(self, **kwargs):
            seen.update(kwargs)

    monkeypatch.setattr(client, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(
        client,
        "settings",
        replace(settings, openrouter_api_key="test-key", llm_timeout_seconds=60),
    )

    client._client()  # noqa: SLF001

    assert seen["timeout"] == 60


def test_the_answer_budget_is_configured_below_the_gateway_limit():
    # The gateway returned 504 for answers that ran past it. The default must stay under 30 s.
    assert settings.answer_budget_seconds <= 25
