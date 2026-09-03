"""Client for OSRM (Open Source Routing Machine)'s public demo server — real
driving distance/duration over the actual road network, not a straight-line
estimate. Free, no API key.

The public demo instance is a best-effort service (not meant for heavy
production use) — see app/features/travel.py for the fallback used when it's
unreachable.
"""

import httpx

BASE_URL = "https://router.project-osrm.org/route/v1/driving"


class RoutingError(Exception):
    pass


class OsrmClient:
    def __init__(self, timeout: float = 8.0) -> None:
        self.timeout = timeout

    def route(self, from_lat: float, from_lon: float, to_lat: float, to_lon: float) -> tuple[float, float]:
        """Returns (distance_km, duration_hours) for the fastest driving
        route, or raises RoutingError."""
        coords = f"{from_lon},{from_lat};{to_lon},{to_lat}"  # OSRM wants lon,lat
        try:
            response = httpx.get(
                f"{BASE_URL}/{coords}",
                params={"overview": "false"},
                headers={"User-Agent": "juve-momentum-index/1.0"},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RoutingError(f"routing service unreachable: {exc}") from exc

        payload = response.json()
        if payload.get("code") != "Ok" or not payload.get("routes"):
            raise RoutingError(f"no route found: {payload.get('code')}")

        route = payload["routes"][0]
        return route["distance"] / 1000.0, route["duration"] / 3600.0
