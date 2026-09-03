import re
from dataclasses import dataclass
from datetime import datetime

from app.core.constants import SOURCE_FOOTBALL_DATA, SOURCE_WIKIPEDIA, TEAM_NAME
from app.core.teams import resolve_alias

JUVENTUS_ALIASES = {"juventus", "juventus fc", "juve"}

_WHITESPACE_RE = re.compile(r"\s+")


def _strip_periods(name: str) -> str:
    """Wikipedia's official team names vary in punctuation between seasons'
    articles (e.g. "AC Milan" one year, "A.C. Milan" the next, for the same
    club) even though the club itself hasn't changed. Left unnormalized,
    each variant is treated as a distinct team, which silently resets that
    team's Elo history and fragments head-to-head stats every time the
    punctuation style flips. Periods carry no identity here, so stripping
    them (and collapsing the resulting double spaces) collapses "A.C. Milan"
    and "AC Milan" back into one name."""
    return _WHITESPACE_RE.sub(" ", name.replace(".", "")).strip()


def canonicalize_team_name(name: str) -> str:
    """Normalizes punctuation variants of the same club name, maps Juventus
    specifically to TEAM_NAME regardless of source spelling (football-data.org
    uses "Juventus FC", the Wikipedia scraper uses whatever label is on the
    results grid), and — for other clubs — resolves known alternate spellings
    (see app.core.teams) to the canonical name already used throughout this
    codebase. Required for the elo/momentum "is this Juve" filter, and for
    Elo/head-to-head continuity for every other club, to work across sources
    and seasons.

    Any name not covered by app.core.teams' alias map falls back to the
    period-stripped form as-is, same as before that module existed — a
    missing alias means a club's Elo history could fragment across a naming
    variant we haven't seen yet, not a crash. Run scripts/check_team_names.py
    after an ingestion to find gaps."""
    normalized = _strip_periods(name)
    if normalized.strip().lower() in JUVENTUS_ALIASES:
        return TEAM_NAME
    return resolve_alias(normalized) or normalized


@dataclass(frozen=True)
class MatchIn:
    external_id: str | None
    season: str
    competition: str
    competition_code: str
    match_date: datetime
    home_team: str
    away_team: str
    home_goals: int | None
    away_goals: int | None
    venue: str | None
    status: str
    source: str


def _season_label(start_year: int) -> str:
    return f"{start_year}-{start_year + 1}"


def normalize_football_data_match(raw: dict) -> MatchIn:
    """Maps a football-data.org v4 `match` object to our common schema."""
    competition = raw["competition"]
    score = raw.get("score", {}).get("fullTime", {})
    match_date = datetime.fromisoformat(raw["utcDate"].replace("Z", "+00:00"))

    season_start = raw.get("season", {}).get("startDate")
    start_year = int(season_start[:4]) if season_start else match_date.year

    return MatchIn(
        external_id=str(raw["id"]),
        season=_season_label(start_year),
        competition=competition["name"],
        competition_code=competition["code"],
        match_date=match_date,
        home_team=canonicalize_team_name(raw["homeTeam"]["name"]),
        away_team=canonicalize_team_name(raw["awayTeam"]["name"]),
        home_goals=score.get("home"),
        away_goals=score.get("away"),
        venue=raw.get("venue"),
        status=raw["status"],
        source=SOURCE_FOOTBALL_DATA,
    )


def normalize_wikipedia_row(
    row: dict,
    season: str,
    competition: str,
    competition_code: str,
) -> MatchIn:
    """Maps one parsed Wikipedia results-table row to our common schema.

    `row` is expected to already have been parsed into plain fields by the
    scraper (see wikipedia_scraper.py) — this function only handles the
    shape/status normalization shared with the API path.
    """
    home_goals = row.get("home_goals")
    away_goals = row.get("away_goals")
    status = "FINISHED" if home_goals is not None and away_goals is not None else "SCHEDULED"

    return MatchIn(
        external_id=None,
        season=season,
        competition=competition,
        competition_code=competition_code,
        match_date=row["match_date"],
        home_team=canonicalize_team_name(row["home_team"]),
        away_team=canonicalize_team_name(row["away_team"]),
        home_goals=home_goals,
        away_goals=away_goals,
        venue=None,  # Wikipedia's results grid doesn't carry venue information
        status=status,
        source=SOURCE_WIKIPEDIA,
    )
