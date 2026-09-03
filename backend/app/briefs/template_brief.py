from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.juve_momentum import JuveMomentum
from app.schemas.brief import BriefData

RESULT_POINTS = {"W": 3, "D": 1, "L": 0}
RESULT_LABELS_IT = {"W": "vinto", "D": "pareggiato", "L": "perso"}
TREND_LABELS_IT = {"up": "in crescita", "down": "in calo", "flat": "stabile"}


def _elo_trend(elos: list[float]) -> str:
    if len(elos) < 2:
        return "flat"
    delta = elos[-1] - elos[0]
    if delta > 5:
        return "up"
    if delta < -5:
        return "down"
    return "flat"


def _head_to_head(db: Session, opponent: str, n: int = 5) -> str | None:
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
    return f"{wins}V-{draws}N-{losses}P nelle ultime {len(rows)} sfide"


def build_pre_match_brief_data(db: Session, opponent: str | None, n: int = 5) -> BriefData:
    """Uses the last N played matches (any opponent) to describe current form."""
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

    return BriefData(
        kind="pre",
        opponent=opponent,
        matches_considered=len(rows),
        avg_momentum=avg_momentum,
        avg_points=avg_points,
        avg_goal_diff=avg_goal_diff,
        elo_trend=elo_trend,
        head_to_head_recent=_head_to_head(db, opponent) if opponent else None,
    )


def build_post_match_brief_data(db: Session, match_id: int, n: int = 5) -> BriefData:
    """`avg_points`/`avg_goal_diff` reuse the stored rolling-5 baseline
    (form GOING INTO this match), so the brief can say whether today's
    performance was above or below recent form."""
    row = db.scalar(select(JuveMomentum).where(JuveMomentum.match_id == match_id))
    if row is None:
        raise ValueError(f"No juve_momentum row for match_id={match_id}")

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
        head_to_head_recent=_head_to_head(db, row.opponent, n),
    )


def render_template_text(data: BriefData) -> list[str]:
    if data.kind == "pre":
        return _render_pre_match(data)
    return _render_post_match(data)


def _render_pre_match(data: BriefData) -> list[str]:
    opponent_str = f" contro {data.opponent}" if data.opponent else ""
    if data.matches_considered == 0:
        return [f"Nessun dato storico disponibile per generare un brief pre-partita{opponent_str}."]

    lines = [
        f"La Juve arriva alla prossima partita{opponent_str} con un Momentum Index medio di "
        f"{data.avg_momentum:.1f}/100 nelle ultime {data.matches_considered} partite.",
        f"Media di {data.avg_points:.2f} punti a partita e differenza reti media di "
        f"{data.avg_goal_diff:+.2f}, con un trend Elo {TREND_LABELS_IT[data.elo_trend]}.",
    ]
    if data.head_to_head_recent:
        lines.append(f"Precedenti recenti contro {data.opponent}: {data.head_to_head_recent}.")
    return lines


def _render_post_match(data: BriefData) -> list[str]:
    lines = [
        f"La Juve ha {RESULT_LABELS_IT[data.result]} {data.goals_for}-{data.goals_against} contro "
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
    return lines
