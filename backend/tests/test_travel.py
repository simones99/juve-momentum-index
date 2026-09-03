from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.features.travel import (
    build_travel_estimate,
    estimate_day_trip,
    estimate_effort_score,
    estimate_fallback_travel,
)

ROME = ZoneInfo("Europe/Rome")
SATURDAY_EVENING = datetime(2026, 9, 5, 18, 0, tzinfo=ROME)  # confirmed Saturday
TUESDAY_LUNCHTIME = datetime(2026, 9, 8, 12, 30, tzinfo=ROME)  # confirmed Tuesday


def test_short_weekend_trip_scores_low_effort():
    score = estimate_effort_score(duration_hours=1.0, kickoff=SATURDAY_EVENING)
    assert score < 15


def test_long_weekday_early_kickoff_scores_high_effort():
    score = estimate_effort_score(duration_hours=8.0, kickoff=TUESDAY_LUNCHTIME)
    assert score > 60


def test_effort_score_increases_with_duration_holding_kickoff_fixed():
    short = estimate_effort_score(duration_hours=1.0, kickoff=SATURDAY_EVENING)
    long = estimate_effort_score(duration_hours=6.0, kickoff=SATURDAY_EVENING)
    assert long > short


def test_effort_score_weekday_penalty_exceeds_weekend_holding_duration_fixed():
    weekend = estimate_effort_score(duration_hours=3.0, kickoff=SATURDAY_EVENING)
    weekday = estimate_effort_score(
        duration_hours=3.0, kickoff=TUESDAY_LUNCHTIME.replace(hour=18)
    )
    assert weekday > weekend


def test_effort_score_stays_within_bounds():
    score = estimate_effort_score(duration_hours=50.0, kickoff=TUESDAY_LUNCHTIME)
    assert 0.0 <= score <= 100.0


def test_short_evening_weekend_trip_is_day_trip_feasible():
    feasible, departure_hour, return_hour = estimate_day_trip(duration_hours=1.5, kickoff=SATURDAY_EVENING)
    assert feasible is True
    assert departure_hour > 4.0
    assert return_hour < 26.0


def test_very_long_early_kickoff_trip_is_not_day_trip_feasible():
    early_far = TUESDAY_LUNCHTIME.replace(hour=12, minute=30)
    feasible, departure_hour, _ = estimate_day_trip(duration_hours=9.0, kickoff=early_far)
    assert feasible is False
    assert departure_hour < 4.0  # would need to leave before dawn (or the night before)


def test_naive_kickoff_datetime_is_treated_as_italy_local():
    naive = datetime(2026, 9, 5, 18, 0)  # no tzinfo
    aware = SATURDAY_EVENING
    assert estimate_effort_score(2.0, naive) == pytest.approx(estimate_effort_score(2.0, aware))


def test_fallback_travel_returns_plausible_positive_values():
    rome = (41.9341, 12.4547)
    milan = (45.4781, 9.1240)
    distance_km, duration_hours = estimate_fallback_travel(rome, milan)
    assert 400 < distance_km < 800  # geodesic ~477km * 1.25 correction
    assert duration_hours > 0


def test_build_travel_estimate_combines_fields_and_marks_estimated_flag():
    estimate = build_travel_estimate(
        distance_km=100.0, duration_hours=1.5, is_estimated=True, kickoff=SATURDAY_EVENING
    )
    assert estimate.distance_km == 100.0
    assert estimate.duration_hours == 1.5
    assert estimate.is_estimated is True
    assert estimate.day_trip_feasible is True
    assert 0.0 <= estimate.effort_score <= 100.0
