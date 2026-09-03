from datetime import datetime, timezone

from sqlalchemy import select

from app.core.constants import COMPETITION_SERIE_A, MATCH_STATUS_FINISHED, SOURCE_FOOTBALL_DATA, TEAM_NAME
from app.features.recompute import recompute_all_derived
from app.models.elo_rating import EloRating
from app.models.juve_momentum import JuveMomentum
from app.models.match import Match

SAME_DATE = datetime(2024, 9, 1, 18, 45, tzinfo=timezone.utc)


def _match(**overrides) -> Match:
    defaults = dict(
        external_id=None,
        season="2024-2025",
        competition="Serie A",
        competition_code=COMPETITION_SERIE_A,
        match_date=SAME_DATE,
        home_team=TEAM_NAME,
        away_team="Inter",
        home_goals=1,
        away_goals=0,
        status=MATCH_STATUS_FINISHED,
        source=SOURCE_FOOTBALL_DATA,
    )
    defaults.update(overrides)
    return Match(**defaults)


def test_recompute_covers_all_teams_in_elo_but_only_juve_in_momentum(db):
    db.add(_match(external_id="juve-milan", home_team=TEAM_NAME, away_team="Milan", home_goals=2, away_goals=1))
    db.add(_match(external_id="inter-roma", home_team="Inter", away_team="Roma", home_goals=0, away_goals=0))
    db.commit()

    recompute_all_derived(db)
    db.commit()

    elo_teams = set(db.scalars(select(EloRating.team)))
    assert elo_teams == {TEAM_NAME, "Milan", "Inter", "Roma"}

    momentum_opponents = list(db.scalars(select(JuveMomentum.opponent)))
    assert momentum_opponents == ["Milan"]


def test_recompute_is_deterministic_across_repeated_calls(db):
    db.add(_match(external_id="a", home_team=TEAM_NAME, away_team="Milan", home_goals=2, away_goals=0))
    db.add(_match(external_id="b", home_team="Inter", away_team="Roma", home_goals=1, away_goals=1))
    db.commit()

    recompute_all_derived(db)
    db.commit()
    first_pass_elo = {
        (r.match_id, r.team): (float(r.elo_before), float(r.elo_after))
        for r in db.scalars(select(EloRating))
    }
    first_pass_momentum = {
        r.match_id: float(r.momentum_index) for r in db.scalars(select(JuveMomentum))
    }

    recompute_all_derived(db)
    db.commit()
    second_pass_elo = {
        (r.match_id, r.team): (float(r.elo_before), float(r.elo_after))
        for r in db.scalars(select(EloRating))
    }
    second_pass_momentum = {
        r.match_id: float(r.momentum_index) for r in db.scalars(select(JuveMomentum))
    }

    assert first_pass_elo == second_pass_elo
    assert first_pass_momentum == second_pass_momentum


def test_same_match_date_ties_are_broken_by_id_order(db):
    """Two Juve matches sharing an identical match_date (e.g. Wikipedia's
    season-start placeholder date) must always be processed in the same
    relative order across runs — here, insertion/id order — so the second
    match's elo_before is always the first match's elo_after, never the
    other way around depending on incidental DB ordering."""
    first = _match(external_id="first", home_team=TEAM_NAME, away_team="Milan", home_goals=3, away_goals=0)
    db.add(first)
    db.flush()  # assign an id to `first` before adding `second`, so id order == insertion order

    second = _match(external_id="second", home_team=TEAM_NAME, away_team="Roma", home_goals=1, away_goals=1)
    db.add(second)
    db.commit()

    assert first.id < second.id  # sanity check on the ordering we're about to rely on

    recompute_all_derived(db)
    db.commit()

    first_row = db.scalar(select(JuveMomentum).where(JuveMomentum.match_id == first.id))
    second_row = db.scalar(select(JuveMomentum).where(JuveMomentum.match_id == second.id))

    assert float(first_row.elo_after) == float(second_row.elo_before)
