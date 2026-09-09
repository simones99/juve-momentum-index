"""Client for the football-data.org v4 API (free tier).

Free tier limits (as of writing): 10 requests/minute, access to a fixed set
of competitions including Serie A (SA) and the Champions League (CL). Auth is
via the `X-Auth-Token` header, not a query string.

Every response carries two quota headers (see
https://docs.football-data.org/general/v4/lookup_tables.html#_response_headers):
`X-RequestsAvailable` (requests left before being blocked) and
`X-RequestCounter-Reset` (seconds until the counter resets). We track those
and back off proactively once the quota is exhausted, instead of only
reacting to a 429 after the fact.
"""

import time

import httpx

BASE_URL = "https://api.football-data.org/v4"
DEFAULT_MIN_REQUEST_INTERVAL_SECONDS = 6.5  # fallback spacing, used until we've seen quota headers


class FootballDataError(Exception):
    pass


class FootballDataRateLimitError(FootballDataError):
    pass


class FootballDataClient:
    def __init__(
        self,
        api_key: str,
        timeout: float = 15.0,
        min_request_interval_seconds: float = DEFAULT_MIN_REQUEST_INTERVAL_SECONDS,
    ) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self.min_request_interval_seconds = min_request_interval_seconds
        self._last_request_at: float | None = None
        self._requests_available: int | None = None
        self._quota_reset_at: float | None = None  # monotonic deadline

    def _throttle(self) -> None:
        now = time.monotonic()
        if self._requests_available is not None and self._requests_available <= 0:
            wait = (self._quota_reset_at - now) if self._quota_reset_at is not None else 10.0
            if wait > 0:
                time.sleep(wait)
            # Quota is unknown again until the next response tells us otherwise.
            self._requests_available = None
            self._quota_reset_at = None
            return
        if self._last_request_at is not None:
            elapsed = now - self._last_request_at
            remaining = self.min_request_interval_seconds - elapsed
            if remaining > 0:
                time.sleep(remaining)

    def _update_quota_from_headers(self, headers: httpx.Headers) -> None:
        available = headers.get("X-RequestsAvailable")
        reset_seconds = headers.get("X-RequestCounter-Reset")
        if available is not None:
            try:
                self._requests_available = int(available)
            except ValueError:
                pass
        if reset_seconds is not None:
            try:
                self._quota_reset_at = time.monotonic() + float(reset_seconds)
            except ValueError:
                pass

    def _get(self, path: str, params: dict | None = None, max_retries: int = 3) -> dict:
        if not self.api_key:
            raise FootballDataError("FOOTBALL_DATA_API_KEY is not configured")

        headers = {"X-Auth-Token": self.api_key}
        for attempt in range(max_retries):
            self._throttle()
            self._last_request_at = time.monotonic()
            response = httpx.get(f"{BASE_URL}{path}", headers=headers, params=params, timeout=self.timeout)
            self._update_quota_from_headers(response.headers)
            if response.status_code == 429:
                if attempt == max_retries - 1:
                    raise FootballDataRateLimitError("football-data.org rate limit exceeded")
                retry_after = float(response.headers.get("Retry-After", "10"))
                self._requests_available = 0
                self._quota_reset_at = time.monotonic() + retry_after
                time.sleep(retry_after)
                continue
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                # e.g. 403 for a season outside the free-tier's rolling window —
                # surfaced as FootballDataError so callers (see ingest.py) can
                # catch it per (season, competition) and fall back/skip instead
                # of the whole ingestion run crashing on one out-of-range season.
                raise FootballDataError(str(exc)) from exc
            return response.json()
        raise FootballDataRateLimitError("football-data.org rate limit exceeded")

    def get_competition_matches(self, competition_code: str, season: str) -> list[dict]:
        """All matches for an entire competition/season (e.g. every Serie A
        fixture, not just Juventus'), so every team gets a real Elo history
        instead of starting fresh at 1500 the first time it meets Juve.
        `season` is the starting year, e.g. "2024" for the 2024-2025 season."""
        data = self._get(f"/competitions/{competition_code}/matches", params={"season": season})
        return data.get("matches", [])

    def get_match(self, external_id: str) -> dict:
        """A single match by its football-data.org id — unlike the
        competition/season list endpoint, this returns the match object
        directly (confirmed against the live API: no wrapping key). Used by
        the live poller to re-check one specific match's status/score
        without re-downloading the whole competition/season."""
        return self._get(f"/matches/{external_id}")
