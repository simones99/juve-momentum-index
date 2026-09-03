"""Client for the football-data.org v4 API (free tier).

Free tier limits (as of writing): 10 requests/minute, access to a fixed set
of competitions including Serie A (SA) and the Champions League (CL). Auth is
via the `X-Auth-Token` header, not a query string.
"""

import time

import httpx

BASE_URL = "https://api.football-data.org/v4"
DEFAULT_MIN_REQUEST_INTERVAL_SECONDS = 6.5  # keeps us under 10 req/min with margin


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

    def _throttle(self) -> None:
        if self._last_request_at is None:
            return
        elapsed = time.monotonic() - self._last_request_at
        remaining = self.min_request_interval_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def _get(self, path: str, params: dict | None = None, max_retries: int = 3) -> dict:
        if not self.api_key:
            raise FootballDataError("FOOTBALL_DATA_API_KEY is not configured")

        headers = {"X-Auth-Token": self.api_key}
        for attempt in range(max_retries):
            self._throttle()
            self._last_request_at = time.monotonic()
            response = httpx.get(f"{BASE_URL}{path}", headers=headers, params=params, timeout=self.timeout)
            if response.status_code == 429:
                if attempt == max_retries - 1:
                    raise FootballDataRateLimitError("football-data.org rate limit exceeded")
                retry_after = float(response.headers.get("Retry-After", "10"))
                time.sleep(retry_after)
                continue
            response.raise_for_status()
            return response.json()
        raise FootballDataRateLimitError("football-data.org rate limit exceeded")

    def get_competition_matches(self, competition_code: str, season: str) -> list[dict]:
        """All matches for an entire competition/season (e.g. every Serie A
        fixture, not just Juventus'), so every team gets a real Elo history
        instead of starting fresh at 1500 the first time it meets Juve.
        `season` is the starting year, e.g. "2024" for the 2024-2025 season."""
        data = self._get(f"/competitions/{competition_code}/matches", params={"season": season})
        return data.get("matches", [])
