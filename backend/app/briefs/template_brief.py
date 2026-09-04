from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import TEAM_NAME
from app.features.elo import INITIAL_ELO
from app.features.win_probability import estimate_match_probabilities
from app.models.elo_rating import EloRating
from app.models.juve_momentum import JuveMomentum
from app.schemas.brief import BriefData

RESULT_POINTS = {"W": 3, "D": 1, "L": 0}
RESULT_LABELS = {
    "it": {"W": "vinto", "D": "pareggiato", "L": "perso"},
    "en": {"W": "won", "D": "drawn", "L": "lost"},
}
TREND_LABELS = {
    "it": {"up": "in crescita", "down": "in calo", "flat": "stabile"},
    "en": {"up": "rising", "down": "falling", "flat": "stable"},
}


def _current_elo(db: Session, team: str) -> float:
    """Most recent known elo_after for `team`, or INITIAL_ELO if the team
    has no rating history yet (never played in the dataset)."""
    rating = db.scalar(
        select(EloRating.elo_after).where(EloRating.team == team).order_by(EloRating.rating_date.desc()).limit(1)
    )
    return float(rating) if rating is not None else INITIAL_ELO


def _elo_before_at_match(db: Session, match_id: int, team: str) -> float | None:
    rating = db.scalar(
        select(EloRating.elo_before).where(EloRating.match_id == match_id, EloRating.team == team)
    )
    return float(rating) if rating is not None else None


def _juve_perspective_probabilities(is_home: bool, juve_elo: float, opponent_elo: float) -> dict[str, float]:
    """estimate_match_probabilities() is keyed by home/away side; this
    reframes its output as {win, draw, loss} from Juventus' perspective
    regardless of which side Juve is on."""
    if is_home:
        probs = estimate_match_probabilities(juve_elo, opponent_elo)
        return {"win": probs["home"], "draw": probs["draw"], "loss": probs["away"]}
    probs = estimate_match_probabilities(opponent_elo, juve_elo)
    return {"win": probs["away"], "draw": probs["draw"], "loss": probs["home"]}


def _elo_trend(elos: list[float]) -> str:
    if len(elos) < 2:
        return "flat"
    delta = elos[-1] - elos[0]
    if delta > 5:
        return "up"
    if delta < -5:
        return "down"
    return "flat"


def _head_to_head(db: Session, opponent: str, n: int = 5, lang: str = "it") -> str | None:
    rows = list(
        db.scalars(
            select(JuveMomentum)
            .where(JuveMomentum.opponent == opponent)
            .order_by(JuveMomentum.match_date.desc())
            .limit(n)
        )
    )
    if not rows:
        return None
    wins = sum(1 for r in rows if r.result == "W")
    draws = sum(1 for r in rows if r.result == "D")
    losses = sum(1 for r in rows if r.result == "L")
    if lang == "en":
        return f"{wins}W-{draws}D-{losses}L in the last {len(rows)} meetings"
    return f"{wins}V-{draws}N-{losses}P nelle ultime {len(rows)} sfide"


def build_pre_match_brief_data(
    db: Session, opponent: str | None, n: int = 5, is_home: bool = True, lang: str = "it"
) -> BriefData:
    """Uses the last N played matches (any opponent) to describe current form.
    `is_home` says whether the upcoming fixture has Juventus at home — it
    only affects the win-probability estimate (home advantage applies to
    whichever side is actually playing at home)."""
    rows = list(
        db.scalars(select(JuveMomentum).order_by(JuveMomentum.match_date.desc()).limit(n))
    )
    rows = list(reversed(rows))  # chronological, oldest first

    if not rows:
        return BriefData(kind="pre", opponent=opponent, matches_considered=0)

    avg_momentum = sum(float(r.momentum_index) for r in rows) / len(rows)
    avg_points = sum(RESULT_POINTS[r.result] for r in rows) / len(rows)
    avg_goal_diff = sum(r.goals_for - r.goals_against for r in rows) / len(rows)
    elo_trend = _elo_trend([float(r.elo_after) for r in rows])

    win_probability = draw_probability = loss_probability = None
    if opponent:
        juve_elo = _current_elo(db, TEAM_NAME)
        opponent_elo = _current_elo(db, opponent)
        probs = _juve_perspective_probabilities(is_home, juve_elo, opponent_elo)
        win_probability, draw_probability, loss_probability = probs["win"], probs["draw"], probs["loss"]

    return BriefData(
        kind="pre",
        opponent=opponent,
        matches_considered=len(rows),
        avg_momentum=avg_momentum,
        avg_points=avg_points,
        avg_goal_diff=avg_goal_diff,
        elo_trend=elo_trend,
        head_to_head_recent=_head_to_head(db, opponent, lang=lang) if opponent else None,
        win_probability=win_probability,
        draw_probability=draw_probability,
        loss_probability=loss_probability,
    )


def build_post_match_brief_data(db: Session, match_id: int, n: int = 5, lang: str = "it") -> BriefData:
    """`avg_points`/`avg_goal_diff` reuse the stored rolling-5 baseline
    (form GOING INTO this match), so the brief can say whether today's
    performance was above or below recent form."""
    row = db.scalar(select(JuveMomentum).where(JuveMomentum.match_id == match_id))
    if row is None:
        raise ValueError(f"No juve_momentum row for match_id={match_id}")

    win_probability = draw_probability = loss_probability = None
    opponent_elo_before = _elo_before_at_match(db, match_id, row.opponent)
    if opponent_elo_before is not None:
        probs = _juve_perspective_probabilities(
            row.home_away == "H", float(row.elo_before), opponent_elo_before
        )
        win_probability, draw_probability, loss_probability = probs["win"], probs["draw"], probs["loss"]

    return BriefData(
        kind="post",
        opponent=row.opponent,
        match_id=match_id,
        matches_considered=n,
        avg_momentum=float(row.momentum_index),
        avg_points=float(row.points_rolling5) if row.points_rolling5 is not None else None,
        avg_goal_diff=float(row.goal_diff_rolling5) if row.goal_diff_rolling5 is not None else None,
        elo_trend=_elo_trend([float(row.elo_before), float(row.elo_after)]),
        result=row.result,
        goals_for=row.goals_for,
        goals_against=row.goals_against,
        elo_before=float(row.elo_before),
        elo_after=float(row.elo_after),
        head_to_head_recent=_head_to_head(db, row.opponent, n, lang=lang),
        win_probability=win_probability,
        draw_probability=draw_probability,
        loss_probability=loss_probability,
    )


def render_template_text(data: BriefData, lang: str = "it") -> list[str]:
    if data.kind == "pre":
        return _render_pre_match(data, lang)
    return _render_post_match(data, lang)


def _render_pre_match(data: BriefData, lang: str = "it") -> list[str]:
    if lang == "en":
        return _render_pre_match_en(data)
    return _render_pre_match_it(data)


def _render_post_match(data: BriefData, lang: str = "it") -> list[str]:
    if lang == "en":
        return _render_post_match_en(data)
    return _render_post_match_it(data)


def _render_pre_match_it(data: BriefData) -> list[str]:
    opponent_str = f" contro {data.opponent}" if data.opponent else ""
    if data.matches_considered == 0:
        return [f"Nessun dato storico disponibile per generare un brief pre-partita{opponent_str}."]

    lines = [
        f"La Juve arriva alla prossima partita{opponent_str} con un Momentum Index medio di "
        f"{data.avg_momentum:.1f}/100 nelle ultime {data.matches_considered} partite.",
        f"Media di {data.avg_points:.2f} punti a partita e differenza reti media di "
        f"{data.avg_goal_diff:+.2f}, con un trend Elo {TREND_LABELS['it'][data.elo_trend]}.",
    ]
    if data.head_to_head_recent:
        lines.append(f"Precedenti recenti contro {data.opponent}: {data.head_to_head_recent}.")
    if data.win_probability is not None:
        lines.append(
            f"Secondo il modello Elo: Juve {data.win_probability * 100:.0f}%, pareggio "
            f"{data.draw_probability * 100:.0f}%, {data.opponent} {data.loss_probability * 100:.0f}%."
        )
    return lines


def _render_pre_match_en(data: BriefData) -> list[str]:
    opponent_str = f" against {data.opponent}" if data.opponent else ""
    if data.matches_considered == 0:
        return [f"No historical data available to generate a pre-match brief{opponent_str}."]

    lines = [
        f"Juve go into the next match{opponent_str} with an average Momentum Index of "
        f"{data.avg_momentum:.1f}/100 over the last {data.matches_considered} matches.",
        f"Averaging {data.avg_points:.2f} points per match and a goal difference of "
        f"{data.avg_goal_diff:+.2f}, with an Elo trend that is {TREND_LABELS['en'][data.elo_trend]}.",
    ]
    if data.head_to_head_recent:
        lines.append(f"Recent head-to-head against {data.opponent}: {data.head_to_head_recent}.")
    if data.win_probability is not None:
        lines.append(
            f"According to the Elo model: Juve {data.win_probability * 100:.0f}%, draw "
            f"{data.draw_probability * 100:.0f}%, {data.opponent} {data.loss_probability * 100:.0f}%."
        )
    return lines


def _render_post_match_it(data: BriefData) -> list[str]:
    lines = [
        f"La Juve ha {RESULT_LABELS['it'][data.result]} {data.goals_for}-{data.goals_against} contro "
        f"{data.opponent}, con l'Elo che passa da {data.elo_before:.0f} a {data.elo_after:.0f}.",
        f"Momentum Index della partita: {data.avg_momentum:.1f}/100.",
    ]
    if data.avg_points is not None and data.avg_goal_diff is not None:
        lines.append(
            f"Prima di questa gara la media delle ultime partite era di {data.avg_points:.2f} punti "
            f"e {data.avg_goal_diff:+.2f} di differenza reti: la prestazione odierna va valutata su "
            "questo confronto."
        )
    if data.head_to_head_recent:
        lines.append(f"Precedenti recenti contro {data.opponent}: {data.head_to_head_recent}.")
    if data.win_probability is not None:
        predicted = {"W": data.win_probability, "D": data.draw_probability, "L": data.loss_probability}[
            data.result
        ]
        lines.append(f"Il modello Elo dava questo esito al {predicted * 100:.0f}% prima del fischio d'inizio.")
    return lines


def _render_post_match_en(data: BriefData) -> list[str]:
    lines = [
        f"Juve {RESULT_LABELS['en'][data.result]} {data.goals_for}-{data.goals_against} against "
        f"{data.opponent}, with Elo moving from {data.elo_before:.0f} to {data.elo_after:.0f}.",
        f"Match Momentum Index: {data.avg_momentum:.1f}/100.",
    ]
    if data.avg_points is not None and data.avg_goal_diff is not None:
        lines.append(
            f"Going into this match the recent-form average was {data.avg_points:.2f} points "
            f"and a goal difference of {data.avg_goal_diff:+.2f}: today's performance should be "
            "read against that baseline."
        )
    if data.head_to_head_recent:
        lines.append(f"Recent head-to-head against {data.opponent}: {data.head_to_head_recent}.")
    if data.win_probability is not None:
        predicted = {"W": data.win_probability, "D": data.draw_probability, "L": data.loss_probability}[
            data.result
        ]
        lines.append(f"The Elo model gave this outcome a {predicted * 100:.0f}% chance before kickoff.")
    return lines
