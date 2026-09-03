"""Away-trip "how hard is it to go" estimate: combines a real driving
duration (from OSRM, see ingestion/routing.py — falls back to a corrected
straight-line estimate only when OSRM is unreachable, see
estimate_fallback_travel) with the fixture's day-of-week and kickoff time
into a single 0-100 effort score, plus a same-day round-trip feasibility
check.

Kickoff-time-of-day matters here (weekday penalty, early/late kickoff
penalty, day-trip departure/return window), so every kickoff datetime is
normalized to Europe/Rome local time first — DB session timezone
configuration must never be relied on for this (see _to_italy_local).

This is a simplified heuristic (same spirit as elo.py / win_probability.py):
the travel duration is real when OSRM answers, but the "is this trip
reasonable" scoring (weights, thresholds) is a hand-picked judgment call,
not fitted to any survey of actual matchgoing fans.
"""

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from geopy.distance import geodesic

ITALY_TZ = ZoneInfo("Europe/Rome")

# Fallback-only: used when OSRM can't be reached. Italian road-network
# distance is typically longer than straight-line due to terrain/routing;
# this is a rough correction factor, not a fitted value.
ROAD_DISTANCE_CORRECTION_FACTOR = 1.25
FALLBACK_AVERAGE_SPEED_KMH = 80.0

# Effort score weights/thresholds
DURATION_SCORE_CAP_HOURS = 9.0  # duration at/above this maps to the max duration sub-score
WEEKDAY_PENALTY = {0: 25, 1: 25, 2: 25, 3: 25, 4: 10, 5: 0, 6: 0}  # Mon=0 .. Sun=6
EARLY_LATE_KICKOFF_PENALTY = 10
EARLY_KICKOFF_HOUR = 14
LATE_KICKOFF_HOUR = 20

# Day-trip feasibility window
STADIUM_ARRIVAL_BUFFER_HOURS = 1.5  # arrive before kickoff
POST_MATCH_HOURS = 2.5  # match + time to get back on the road
EARLIEST_REASONABLE_DEPARTURE_HOUR = 4.0
LATEST_REASONABLE_RETURN_HOUR = 26.0  # 02:00 the next day


@dataclass(frozen=True)
class TravelEstimate:
    distance_km: float
    duration_hours: float
    is_estimated: bool  # True when OSRM was unreachable and this is the geodesic fallback
    effort_score: float
    day_trip_feasible: bool
    departure_hour: float  # local hour-of-day you'd need to leave by (can be negative = "the day before")
    return_hour: float  # local hour-of-day you'd get back (can exceed 24 = "after midnight")


def _to_italy_local(kickoff: datetime) -> datetime:
    if kickoff.tzinfo is None:
        return kickoff.replace(tzinfo=ITALY_TZ)
    return kickoff.astimezone(ITALY_TZ)


def estimate_fallback_travel(
    from_coords: tuple[float, float], to_coords: tuple[float, float]
) -> tuple[float, float]:
    """Straight-line distance corrected for typical Italian road-network
    detour, used ONLY when real routing (OSRM) is unreachable. Callers must
    mark results built from this as is_estimated=True."""
    straight_line_km = geodesic(from_coords, to_coords).km
    distance_km = straight_line_km * ROAD_DISTANCE_CORRECTION_FACTOR
    duration_hours = distance_km / FALLBACK_AVERAGE_SPEED_KMH
    return distance_km, duration_hours


def estimate_effort_score(duration_hours: float, kickoff: datetime) -> float:
    local_kickoff = _to_italy_local(kickoff)
    duration_score = min(duration_hours / DURATION_SCORE_CAP_HOURS, 1.0) * 100
    weekday_penalty = WEEKDAY_PENALTY[local_kickoff.weekday()]
    time_penalty = (
        EARLY_LATE_KICKOFF_PENALTY
        if (local_kickoff.hour < EARLY_KICKOFF_HOUR or local_kickoff.hour >= LATE_KICKOFF_HOUR)
        else 0
    )
    score = 0.7 * duration_score + 0.2 * weekday_penalty + 0.1 * time_penalty
    return max(0.0, min(100.0, score))


def estimate_day_trip(duration_hours: float, kickoff: datetime) -> tuple[bool, float, float]:
    local_kickoff = _to_italy_local(kickoff)
    kickoff_hour = local_kickoff.hour + local_kickoff.minute / 60
    departure_hour = kickoff_hour - duration_hours - STADIUM_ARRIVAL_BUFFER_HOURS
    return_hour = kickoff_hour + POST_MATCH_HOURS + duration_hours
    feasible = departure_hour >= EARLIEST_REASONABLE_DEPARTURE_HOUR and return_hour <= LATEST_REASONABLE_RETURN_HOUR
    return feasible, departure_hour, return_hour


def build_travel_estimate(
    distance_km: float, duration_hours: float, is_estimated: bool, kickoff: datetime
) -> TravelEstimate:
    effort_score = estimate_effort_score(duration_hours, kickoff)
    feasible, departure_hour, return_hour = estimate_day_trip(duration_hours, kickoff)
    return TravelEstimate(
        distance_km=distance_km,
        duration_hours=duration_hours,
        is_estimated=is_estimated,
        effort_score=effort_score,
        day_trip_feasible=feasible,
        departure_hour=departure_hour,
        return_hour=return_hour,
    )
