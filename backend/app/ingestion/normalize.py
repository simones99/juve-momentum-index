from dataclasses import dataclass
from datetime import datetime

from app.core.constants import SOURCE_FOOTBALL_DATA, SOURCE_WIKIPEDIA, TEAM_NAME

JUVENTUS_ALIASES = {"juventus", "juventus fc", "juve"}


def canonicalize_team_name(name: str) -> str:
    """Juventus appears under different spellings depending on the source
    (football-data.org uses the official "Juventus FC", the Wikipedia
    scraper uses whatever label is on the results grid). Canonicalizing to
    a single name is required for the elo/momentum "is this Juve" filter to
    work across sources."""
    return TEAM_NAME if name.strip().lower() in JUVENTUS_ALIASES else name


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
        status=status,
        source=SOURCE_WIKIPEDIA,
    )
