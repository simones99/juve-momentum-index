"""Frequent, lightweight polling of today's Juventus match(es) while they may
be in progress.

Separate from `app.ingestion.ingest.update_matches`, which downloads a whole
competition/season and runs `recompute_all_derived` — far too heavy to run
every couple of minutes on a matchday. This module only re-checks the
specific match(es) scheduled for today and writes status/score back
directly, with no Elo/momentum recomputation.
"""

import logging
from datetime import date, datetime, time, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import MATCH_STATUS_FINISHED, MATCH_STATUS_IN_PLAY, MATCH_STATUS_POSTPONED, TEAM_NAME
from app.ingestion.football_data_client import FootballDataClient, FootballDataError
from app.models.match import Match
from app.notifications.push_sender import notify_subscribers

logger = logging.getLogger(__name__)

_DONE_STATUSES = (MATCH_STATUS_FINISHED, MATCH_STATUS_POSTPONED)


def _todays_juve_matches(db: Session, today: date) -> list[Match]:
    start = datetime.combine(today, time.min, tzinfo=timezone.utc)
    end = datetime.combine(today, time.max, tzinfo=timezone.utc)
    stmt = select(Match).where(
        (Match.home_team == TEAM_NAME) | (Match.away_team == TEAM_NAME),
        Match.match_date >= start,
        Match.match_date <= end,
        Match.status.not_in(_DONE_STATUSES),
        Match.external_id.is_not(None),
    )
    return list(db.scalars(stmt))


def poll_live_matches(db: Session, client: FootballDataClient) -> list[Match]:
    """Re-checks today's not-yet-finished Juventus match(es) against
    football-data.org and updates `status`/`home_goals`/`away_goals` in
    place. Cheap on days with no Juve match: one fast, indexed DB query and
    no external API call at all. Returns the matches that were re-checked,
    so callers (e.g. a future notification hook) can react to status
    changes.
    """
    matches = _todays_juve_matches(db, date.today())
    updated: list[Match] = []
    kickoffs: list[Match] = []
    for match in matches:
        try:
            raw = client.get_match(match.external_id)
        except FootballDataError as exc:
            logger.warning("live poll failed for match external_id=%s: %s", match.external_id, exc)
            continue
        previous_status = match.status
        score = raw.get("score", {}).get("fullTime", {})
        match.status = raw.get("status", match.status)
        match.home_goals = score.get("home", match.home_goals)
        match.away_goals = score.get("away", match.away_goals)
        updated.append(match)
        if previous_status != MATCH_STATUS_IN_PLAY and match.status == MATCH_STATUS_IN_PLAY:
            kickoffs.append(match)

    if updated:
        db.commit()

    for match in kickoffs:
        opponent = match.away_team if match.home_team == TEAM_NAME else match.home_team
        notify_subscribers(db, "kickoff", {"title": "Kickoff!", "body": f"Juventus – {opponent}"})

    return updated
