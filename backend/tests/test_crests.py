from app.core.constants import TEAM_NAME
from app.core.crests import CRESTS


def test_juventus_crest_is_present():
    assert CRESTS[TEAM_NAME] == "https://crests.football-data.org/109.png"


def test_known_serie_a_club_crest_is_present():
    assert CRESTS["SSC Napoli"] == "https://crests.football-data.org/113.png"


def test_unknown_team_has_no_crest_entry():
    assert "Some Historic Club FC" not in CRESTS


def test_every_key_matches_a_canonical_stadiums_name_or_juventus():
    # Le chiavi devono restare allineate ai nomi canonici già usati altrove
    # (app/core/stadiums.py), altrimenti un lookup per nome squadra fallisce
    # silenziosamente in un posto e non nell'altro.
    from app.core.stadiums import STADIUMS

    known_names = set(STADIUMS.keys()) | {TEAM_NAME}
    assert set(CRESTS.keys()) <= known_names
