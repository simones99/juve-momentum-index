"""One-off diagnostic: after an ingestion, lists every distinct team name
actually stored in `matches` and flags which ones aren't recognized by
app.core.stadiums.STADIUMS (or TEAM_NAME) — i.e. which ones need a new alias
in app.core.teams.ALIASES. Meant to be run right after ingesting from a new
source (e.g. once a real football-data.org API key is available) to quickly
discover naming variants instead of guessing them.

Usage (from backend/):
    python scripts/check_team_names.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.core.constants import TEAM_NAME  # noqa: E402
from app.core.stadiums import STADIUMS  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.models.match import Match  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        home_names = set(db.scalars(select(Match.home_team).distinct()))
        away_names = set(db.scalars(select(Match.away_team).distinct()))
    finally:
        db.close()

    all_names = sorted(home_names | away_names)
    if not all_names:
        print("No matches in the DB yet — nothing to check.")
        return

    recognized, unrecognized = [], []
    for name in all_names:
        if name == TEAM_NAME or name in STADIUMS:
            recognized.append(name)
        else:
            unrecognized.append(name)

    print(f"{len(all_names)} distinct team names in matches.\n")

    print(f"Recognized ({len(recognized)}):")
    for name in recognized:
        print(f"  OK   {name}")

    print(f"\nUNRECOGNIZED ({len(unrecognized)}) — add an alias in app/core/teams.py:")
    for name in unrecognized:
        print(f"  ??   {name}")

    if unrecognized:
        print(
            f"\n{len(unrecognized)} name(s) need attention: they won't match "
            "app.core.stadiums.STADIUMS, so Trasferte will show them without "
            "distance/effort score, and if they're punctuation/spelling "
            "variants of an already-known club their Elo history is "
            "fragmenting across the two spellings."
        )
    else:
        print("\nAll team names recognized.")


if __name__ == "__main__":
    main()
