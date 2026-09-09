from datetime import datetime, timedelta, timezone

import app.ingestion.ingest as ingest
from app.core.constants import COMPETITION_SERIE_A, SOURCE_FOOTBALL_DATA, TEAM_NAME
from app.models.juve_momentum import JuveMomentum
from app.models.match import Match


def _make_match(**overrides) -> Match:
    defaults = dict(
        external_id="fd-1",
        season="2023-2024",
        competition="Serie A",
        competition_code=COMPETITION_SERIE_A,
        match_date=datetime.now(timezone.utc) + timedelta(hours=1),
        home_team=TEAM_NAME,
        away_team="Inter",
        home_goals=None,
        away_goals=None,
        status="TIMED",
        source=SOURCE_FOOTBALL_DATA,
    )
    defaults.update(overrides)
    return Match(**defaults)


def test_brief_ready_notifies_once_for_upcoming_match_within_window(monkeypatch, db):
    match = _make_match(match_date=datetime.now(timezone.utc) + timedelta(hours=24))
    db.add(match)
    db.commit()

    calls = []
    monkeypatch.setattr(ingest, "notify_subscribers", lambda db, event, payload: calls.append((event, payload)))

    ingest._notify_brief_ready(db)

    assert len(calls) == 1
    assert calls[0][0] == "brief"
    assert match.brief_notified_at is not None


def test_brief_ready_does_not_renotify_already_notified_match(monkeypatch, db):
    match = _make_match(
        match_date=datetime.now(timezone.utc) + timedelta(hours=24),
        brief_notified_at=datetime.now(timezone.utc),
    )
    db.add(match)
    db.commit()

    calls = []
    monkeypatch.setattr(ingest, "notify_subscribers", lambda db, event, payload: calls.append((event, payload)))

    ingest._notify_brief_ready(db)

    assert calls == []


def test_brief_ready_ignores_matches_outside_the_window(monkeypatch, db):
    match = _make_match(match_date=datetime.now(timezone.utc) + timedelta(hours=72))
    db.add(match)
    db.commit()

    calls = []
    monkeypatch.setattr(ingest, "notify_subscribers", lambda db, event, payload: calls.append((event, payload)))

    ingest._notify_brief_ready(db)

    assert calls == []


def _add_momentum_row(db, match_date: datetime, momentum_index: float) -> None:
    match = _make_match(
        external_id=f"fd-{match_date.isoformat()}",
        match_date=match_date,
        status="FINISHED",
        home_goals=1,
        away_goals=0,
    )
    db.add(match)
    db.flush()
    db.add(
        JuveMomentum(
            match_id=match.id,
            season="2023-2024",
            match_date=match_date,
            opponent="Inter",
            home_away="H",
            competition_code=COMPETITION_SERIE_A,
            result="W",
            goals_for=1,
            goals_against=0,
            elo_before=1500,
            elo_after=1510,
            elo_normalized=50,
            momentum_index=momentum_index,
        )
    )


def test_momentum_swing_notifies_when_change_exceeds_threshold(monkeypatch, db):
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    for i in range(ingest.MOMENTUM_SWING_LOOKBACK):
        _add_momentum_row(db, base + timedelta(days=i), momentum_index=50.0)
    _add_momentum_row(
        db,
        base + timedelta(days=ingest.MOMENTUM_SWING_LOOKBACK),
        momentum_index=50.0 + ingest.MOMENTUM_SWING_THRESHOLD + 1,
    )
    db.commit()

    calls = []
    monkeypatch.setattr(ingest, "notify_subscribers", lambda db, event, payload: calls.append((event, payload)))

    ingest._notify_momentum_swing(db)

    assert len(calls) == 1
    assert calls[0][0] == "momentum"


def test_momentum_swing_stays_quiet_below_threshold(monkeypatch, db):
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    for i in range(ingest.MOMENTUM_SWING_LOOKBACK + 1):
        _add_momentum_row(db, base + timedelta(days=i), momentum_index=50.0 + i)
    db.commit()

    calls = []
    monkeypatch.setattr(ingest, "notify_subscribers", lambda db, event, payload: calls.append((event, payload)))

    ingest._notify_momentum_swing(db)

    assert calls == []


def test_momentum_swing_does_nothing_with_too_little_history(monkeypatch, db):
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    _add_momentum_row(db, base, momentum_index=90.0)
    db.commit()

    calls = []
    monkeypatch.setattr(ingest, "notify_subscribers", lambda db, event, payload: calls.append((event, payload)))

    ingest._notify_momentum_swing(db)

    assert calls == []
