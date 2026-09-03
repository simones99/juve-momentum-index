"""Wikipedia fallback scraper — used ONLY when football-data.org is
unavailable or missing data for a Serie A season (see ingest.py).

Wikipedia's "20XX-YY Serie A" articles publish a full round-robin results
grid: a square table where row headers are full team names (home side) and
column headers are 3-letter team codes (away side), and cell (row=home,
col=away) holds the score as "H-A". We parse that grid and extract EVERY
match in it (up to 380 for a 20-team Serie A season: 20*19 ordered pairs),
not just Juventus' — ingesting the full league gives every opponent a real
Elo history instead of resetting to INITIAL_ELO on first appearance (see
the limitation note in features/elo.py). Row and column labels are resolved
to the same canonical name per team (see _build_name_map) since the grid
uses two different label systems (full names for rows, codes for columns)
for the same 20 teams.

This is inherently best-effort and more fragile than the API path (page
structure can change between seasons) — it is not on the critical path.

Known limitation: Champions League fallback is not implemented here. The
CL competition format (group stage vs. league phase) has changed across
seasons and a robust scraper would need per-season handling; since
football-data.org is the primary source for CL, this gap is accepted and
documented in the README rather than built out for the MVP.
"""

import logging
import re
from datetime import datetime
from io import StringIO

import httpx
import pandas as pd
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SCORE_PATTERN = re.compile(r"^\s*(\d+)\s*[-–]\s*(\d+)\s*$")


def _season_wikipedia_title(season: str) -> str:
    # "2023-2024" -> "2023-24 Serie A"
    start, end = season.split("-")
    return f"{start}-{end[2:]} Serie A"


def _fetch_page(title: str) -> tuple[str, list[pd.DataFrame]]:
    url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
    response = httpx.get(url, timeout=20.0, headers={"User-Agent": "juve-momentum-index/1.0"})
    response.raise_for_status()
    html = response.text
    return html, pd.read_html(StringIO(html))


def _find_grid_table(soup: BeautifulSoup, anchor_label: str) -> object | None:
    """Locates the actual <table> DOM node behind the pandas-parsed results
    grid, by finding a table whose headers include a known column code from
    that grid (any one of them works as an anchor) among ~20 header cells."""
    for table in soup.find_all("table"):
        header_texts = {th.get_text(strip=True) for th in table.find_all("th")}
        if anchor_label in header_texts and len(header_texts) >= 15:
            return table
    return None


def _build_name_map(table, wanted_texts: set[str]) -> dict[str, str]:
    """Row headers show full display names (e.g. "Atalanta") and column
    headers show 3-letter codes (e.g. "ATA") for the SAME team, and neither
    is Wikipedia's canonical name. Both are rendered as
    `<th><a title="Atalanta BC">...</a></th>`, so resolving both through the
    same title attribute gives one consistent name per team — otherwise a
    team would show up under two or three different spellings depending on
    whether it appeared as a row or a column, silently fragmenting its Elo
    history and head-to-head stats."""
    mapping: dict[str, str] = {}
    for th in table.find_all("th"):
        text = th.get_text(strip=True)
        if text in wanted_texts and text not in mapping:
            link = th.find("a")
            if link and link.get("title"):
                mapping[text] = link["title"]
    return mapping


def _looks_like_results_grid(df: pd.DataFrame) -> bool:
    if df.shape[0] < 10 or df.shape[1] < 10:
        return False
    if df.shape[0] != df.shape[1] and abs(df.shape[0] - df.shape[1]) > 1:
        return False
    sample_cells = df.iloc[:5, 1:6].astype(str).values.flatten()
    return any(SCORE_PATTERN.match(c) for c in sample_cells)


def scrape_serie_a_season(season: str) -> list[dict]:
    """Returns a list of dicts with keys: match_date, home_team, away_team,
    home_goals, away_goals — ready for normalize_wikipedia_row(). Extracts
    EVERY match in the season's results grid, not just Juventus'.
    match_date is a best-effort placeholder (Wikipedia's grid table has no
    per-match date) set to season start; callers relying on precise dates
    should prefer the football-data.org path.
    """
    title = _season_wikipedia_title(season)
    try:
        html, tables = _fetch_page(title)
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Wikipedia fallback failed to fetch %s: %s", title, exc)
        return []

    grid = next((t for t in tables if _looks_like_results_grid(t)), None)
    if grid is None:
        logger.warning("No results grid found on Wikipedia page %s", title)
        return []

    grid = grid.set_index(grid.columns[0])

    soup = BeautifulSoup(html, "lxml")
    # Any column code works as the anchor to locate the underlying <table>
    # DOM node — nothing about this step is Juventus-specific.
    grid_table = _find_grid_table(soup, str(grid.columns[0]))
    wanted_texts = {str(c) for c in grid.columns} | {str(i) for i in grid.index}
    name_map = _build_name_map(grid_table, wanted_texts) if grid_table is not None else {}

    def resolve(name: str) -> str:
        return name_map.get(name, name)

    start_year = int(season.split("-")[0])
    placeholder_date = datetime(start_year, 8, 15)

    n_teams = len(grid.index)
    expected_matches = n_teams * (n_teams - 1)

    matches: list[dict] = []
    for row_raw in grid.index:
        home_team = resolve(str(row_raw))
        for col_raw in grid.columns:
            away_team = resolve(str(col_raw))
            if home_team == away_team:
                continue  # diagonal: a team's cell against itself
            cell = str(grid.loc[row_raw, col_raw])
            m = SCORE_PATTERN.match(cell)
            if m:
                matches.append(
                    {
                        "match_date": placeholder_date,
                        "home_team": home_team,
                        "away_team": away_team,
                        "home_goals": int(m.group(1)),
                        "away_goals": int(m.group(2)),
                    }
                )

    if len(matches) < expected_matches:
        logger.warning(
            "Extracted %d/%d expected matches from %s results grid (some cells likely carry "
            "non-numeric annotations, e.g. awarded/voided matches, and were skipped)",
            len(matches),
            expected_matches,
            title,
        )
    else:
        logger.info("Extracted %d matches from %s results grid", len(matches), title)

    return matches
