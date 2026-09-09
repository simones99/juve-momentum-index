from datetime import date, datetime, timezone

from app.core.constants import COMPETITION_SERIE_A, SOURCE_FOOTBALL_DATA, TEAM_NAME
from app.ingestion.football_data_client import FootballDataError
from app.live import poller
from app.models.match import Match

TODAY = date(2024, 3, 15)


class _FrozenDate(date):
    @classmethod
    def today(cls):
        return TODAY


def _make_match(**overrides) -> Match:
    defaults = dict(
        external_id="fd-1",
        season="2023-2024",
        competition="Serie A",
        competition_code=COMPETITION_SERIE_A,
        match_date=datetime(2024, 3, 15, 20, 45, tzinfo=timezone.utc),
        home_team=TEAM_NAME,
        away_team="Inter",
        home_goals=None,
        away_goals=None,
        status="TIMED",
        source=SOURCE_FOOTBALL_DATA,
    )
    defaults.update(overrides)
    return Match(**defaults)


class _FakeClient:
    def __init__(self, responses: dict[str, dict] | None = None, error: Exception | None = None):
        self.responses = responses or {}
        self.error = error
        self.calls: list[str] = []

    def get_match(self, external_id: str) -> dict:
        self.calls.append(external_id)
        if self.error:
            raise self.error
        return self.responses[external_id]


def test_no_juve_match_today_makes_no_api_call(monkeypatch, db):
    monkeypatch.setattr(poller, "date", _FrozenDate)
    client = _FakeClient()

    result = poller.poll_live_matches(db, client)

    assert result == []
    assert client.calls == []


def test_updates_status_and_score_for_todays_match(monkeypatch, db):
    monkeypatch.setattr(poller, "date", _FrozenDate)
    match = _make_match()
    db.add(match)
    db.commit()

    client = _FakeClient({"fd-1": {"status": "IN_PLAY", "score": {"fullTime": {"home": 1, "away": 0}}}})
    result = poller.poll_live_matches(db, client)

    assert len(result) == 1
    assert result[0].status == "IN_PLAY"
    assert result[0].home_goals == 1
    assert result[0].away_goals == 0


def test_already_finished_match_is_not_polled(monkeypatch, db):
    monkeypatch.setattr(poller, "date", _FrozenDate)
    db.add(_make_match(status="FINISHED", home_goals=2, away_goals=1))
    db.commit()

    client = _FakeClient()
    result = poller.poll_live_matches(db, client)

    assert result == []
    assert client.calls == []


def test_match_without_external_id_is_skipped(monkeypatch, db):
    # Wikipedia-fallback rows have no external_id and can't be re-fetched
    # from football-data.org's single-match endpoint.
    monkeypatch.setattr(poller, "date", _FrozenDate)
    db.add(_make_match(external_id=None, source="wikipedia"))
    db.commit()

    client = _FakeClient()
    result = poller.poll_live_matches(db, client)

    assert result == []
    assert client.calls == []


def test_match_not_today_is_ignored(monkeypatch, db):
    monkeypatch.setattr(poller, "date", _FrozenDate)
    db.add(_make_match(match_date=datetime(2024, 3, 16, 20, 45, tzinfo=timezone.utc)))
    db.commit()

    client = _FakeClient()
    result = poller.poll_live_matches(db, client)

    assert result == []
    assert client.calls == []


def test_api_error_is_logged_and_skipped_not_raised(monkeypatch, db):
    monkeypatch.setattr(poller, "date", _FrozenDate)
    db.add(_make_match())
    db.commit()

    client = _FakeClient(error=FootballDataError("boom"))
    result = poller.poll_live_matches(db, client)

    assert result == []


def test_kickoff_notification_fires_on_transition_to_in_play(monkeypatch, db):
    monkeypatch.setattr(poller, "date", _FrozenDate)
    db.add(_make_match(status="TIMED"))
    db.commit()

    client = _FakeClient({"fd-1": {"status": "IN_PLAY", "score": {"fullTime": {"home": 0, "away": 0}}}})
    calls = []
    monkeypatch.setattr(poller, "notify_subscribers", lambda db, event, payload: calls.append((event, payload)))

    poller.poll_live_matches(db, client)

    assert len(calls) == 1
    assert calls[0][0] == "kickoff"
    assert "Inter" in calls[0][1]["body"]


def test_kickoff_notification_does_not_refire_when_already_in_play(monkeypatch, db):
    monkeypatch.setattr(poller, "date", _FrozenDate)
    db.add(_make_match(status="IN_PLAY"))
    db.commit()

    client = _FakeClient({"fd-1": {"status": "IN_PLAY", "score": {"fullTime": {"home": 1, "away": 0}}}})
    calls = []
    monkeypatch.setattr(poller, "notify_subscribers", lambda db, event, payload: calls.append((event, payload)))

    poller.poll_live_matches(db, client)

    assert calls == []
