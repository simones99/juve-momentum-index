import time

import httpx
import pytest

from app.ingestion.football_data_client import (
    BASE_URL,
    FootballDataClient,
    FootballDataError,
    FootballDataRateLimitError,
)


def _response(status_code: int, headers: dict | None = None, json_body: dict | None = None) -> httpx.Response:
    request = httpx.Request("GET", f"{BASE_URL}/competitions/SA/matches")
    return httpx.Response(status_code, request=request, headers=headers or {}, json=json_body or {})


def test_403_is_wrapped_as_football_data_error_not_raw_httpx_error(monkeypatch):
    # A season outside the free tier's rolling window returns 403. This must
    # be catchable by ingest.py's per-(season, competition) `except
    # FootballDataError`, not a raw httpx.HTTPStatusError — otherwise one
    # out-of-range season crashes the whole ingestion run instead of
    # gracefully skipping/falling back for just that one.
    monkeypatch.setattr(time, "sleep", lambda *_: None)
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _response(403, json_body={"message": "restricted"}))

    client = FootballDataClient(api_key="fake-key")
    with pytest.raises(FootballDataError):
        client.get_competition_matches("SA", "2019")


def test_quota_headers_trigger_proactive_backoff_before_next_request(monkeypatch):
    sleep_calls: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: sleep_calls.append(s))

    responses = [
        _response(200, headers={"X-RequestsAvailable": "0", "X-RequestCounter-Reset": "42"}, json_body={"matches": []}),
        _response(200, json_body={"matches": []}),
    ]
    monkeypatch.setattr(httpx, "get", lambda *a, **k: responses.pop(0))

    client = FootballDataClient(api_key="fake-key")
    client.get_competition_matches("SA", "2024")  # response says quota is now exhausted
    client.get_competition_matches("SA", "2025")  # must wait out X-RequestCounter-Reset first

    assert sleep_calls, "expected a proactive wait before the second request"
    assert sleep_calls[-1] == pytest.approx(42, abs=0.5)


def test_429_retries_with_retry_after_then_succeeds(monkeypatch):
    sleep_calls: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: sleep_calls.append(s))

    responses = [
        _response(429, headers={"Retry-After": "5"}),
        _response(200, json_body={"matches": [{"id": 1}]}),
    ]
    monkeypatch.setattr(httpx, "get", lambda *a, **k: responses.pop(0))

    client = FootballDataClient(api_key="fake-key")
    matches = client.get_competition_matches("SA", "2024")

    assert matches == [{"id": 1}]
    assert 5.0 in sleep_calls


def test_429_exhausting_all_retries_raises_rate_limit_error(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda *_: None)
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _response(429, headers={"Retry-After": "1"}))

    client = FootballDataClient(api_key="fake-key")
    with pytest.raises(FootballDataRateLimitError):
        client.get_competition_matches("SA", "2024")


def test_missing_api_key_raises_before_any_request(monkeypatch):
    def _fail(*_a, **_k):
        raise AssertionError("should not make an HTTP request without an API key")

    monkeypatch.setattr(httpx, "get", _fail)

    client = FootballDataClient(api_key="")
    with pytest.raises(FootballDataError):
        client.get_competition_matches("SA", "2024")


def test_get_match_returns_the_match_object_directly(monkeypatch):
    # Confirmed against the live API: GET /v4/matches/{id} returns the match
    # fields at the top level, unlike the list endpoints (which wrap results
    # in a "matches" key) — no extra unwrapping needed here.
    monkeypatch.setattr(time, "sleep", lambda *_: None)
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *a, **k: _response(200, json_body={"id": 12345, "status": "IN_PLAY", "score": {}}),
    )

    client = FootballDataClient(api_key="fake-key")
    match = client.get_match("12345")

    assert match == {"id": 12345, "status": "IN_PLAY", "score": {}}
