"""One-off setup helper: resolves the numeric football-data.org team id for
Juventus and prints it so you can set JUVENTUS_TEAM_ID in your .env.

Usage (from backend/, with FOOTBALL_DATA_API_KEY set in the environment or .env):
    python scripts/resolve_team_id.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.core.constants import COMPETITION_SERIE_A, TEAM_NAME  # noqa: E402
from app.ingestion.football_data_client import FootballDataClient  # noqa: E402


def main() -> None:
    settings = get_settings()
    client = FootballDataClient(api_key=settings.football_data_api_key)
    team_id = client.find_team_id_by_name(COMPETITION_SERIE_A, "Juventus")
    if team_id is None:
        print(f"Could not find a team matching '{TEAM_NAME}' in Serie A teams list.")
        raise SystemExit(1)
    print(f"JUVENTUS_TEAM_ID={team_id}")


if __name__ == "__main__":
    main()
