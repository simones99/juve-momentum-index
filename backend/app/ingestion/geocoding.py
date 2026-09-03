"""Client for Nominatim (OpenStreetMap's free geocoding service) — resolves a
free-text place name (e.g. "Ancona") to coordinates, so a user can search for
their departure city without picking from a fixed list.

No API key, but Nominatim's usage policy requires a descriptive User-Agent
and asks for at most ~1 request/second — this client is only called from an
interactive user search (not bulk), so a light client-side throttle is enough
to stay well within that.
"""

import time

import httpx

BASE_URL = "https://nominatim.openstreetmap.org/search"
MIN_REQUEST_INTERVAL_SECONDS = 1.0


class GeocodingError(Exception):
    pass


class NominatimClient:
    def __init__(self, timeout: float = 8.0) -> None:
        self.timeout = timeout
        self._last_request_at: float | None = None

    def _throttle(self) -> None:
        if self._last_request_at is None:
            return
        elapsed = time.monotonic() - self._last_request_at
        remaining = MIN_REQUEST_INTERVAL_SECONDS - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def geocode(self, query: str) -> tuple[float, float, str]:
        """Returns (lat, lon, display_name) for the best match, or raises
        GeocodingError if the query is empty, the service is unreachable, or
        nothing matches."""
        if not query or not query.strip():
            raise GeocodingError("empty query")

        self._throttle()
        self._last_request_at = time.monotonic()
        try:
            response = httpx.get(
                BASE_URL,
                params={"q": query, "format": "json", "limit": 1},
                headers={"User-Agent": "juve-momentum-index/1.0"},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise GeocodingError(f"geocoding service unreachable: {exc}") from exc

        results = response.json()
        if not results:
            raise GeocodingError(f"no location found for '{query}'")

        best = results[0]
        return float(best["lat"]), float(best["lon"]), best["display_name"]
