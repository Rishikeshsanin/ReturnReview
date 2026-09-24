import pytest

from app.services import agent_service
from app.services.agent_service import (
    _generate_with_capacity_fallback,
    _is_capacity_gemini_error,
    _is_transient_gemini_error,
)


class DummyError(Exception):
    def __init__(self, code):
        super().__init__(str(code))
        self.status_code = code


def test_transient_gemini_errors_are_retried():
    for code in (429, 500, 502, 503, 504):
        assert _is_transient_gemini_error(DummyError(code)) is True


def test_auth_error_is_not_retried():
    assert _is_transient_gemini_error(DummyError(401)) is False


def test_capacity_fallback_is_used_only_after_transient_primary_failure(monkeypatch):
    calls = []

    def fake_generate(client, *, model, contents, config):
        calls.append(model)
        if model == "primary":
            raise DummyError(503)
        return "fallback-response"

    monkeypatch.setattr(agent_service, "_generate_with_retry", fake_generate)
    response, model_used = _generate_with_capacity_fallback(
        object(),
        primary_model="primary",
        fallback_model="fallback",
        contents="test",
        config=None,
    )

    assert response == "fallback-response"
    assert model_used == "fallback"
    assert calls == ["primary", "fallback"]


def test_capacity_fallback_does_not_hide_non_transient_errors(monkeypatch):
    def fake_generate(client, *, model, contents, config):
        raise DummyError(401)

    monkeypatch.setattr(agent_service, "_generate_with_retry", fake_generate)
    with pytest.raises(DummyError):
        _generate_with_capacity_fallback(
            object(),
            primary_model="primary",
            fallback_model="fallback",
            contents="test",
            config=None,
        )


class DailyQuotaError(Exception):
    status_code = 429

    def __str__(self):
        return (
            "429 RESOURCE_EXHAUSTED: exceeded your current quota; "
            "GenerateRequestsPerDayPerProjectPerModel-FreeTier free_tier_requests"
        )


def test_daily_quota_is_not_retried_but_can_trigger_capacity_fallback():
    error = DailyQuotaError()
    assert _is_transient_gemini_error(error) is False
    assert _is_capacity_gemini_error(error) is True


def test_daily_quota_primary_uses_fallback_without_hiding_auth_errors(monkeypatch):
    calls = []

    def fake_generate(client, *, model, contents, config):
        calls.append(model)
        if model == "primary":
            raise DailyQuotaError()
        return "fallback-response"

    monkeypatch.setattr(agent_service, "_generate_with_retry", fake_generate)
    response, model_used = _generate_with_capacity_fallback(
        object(),
        primary_model="primary",
        fallback_model="fallback",
        contents="test",
        config=None,
    )

    assert response == "fallback-response"
    assert model_used == "fallback"
    assert calls == ["primary", "fallback"]
