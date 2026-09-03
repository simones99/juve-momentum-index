"""Offline tests for the full-grid Wikipedia scraper — no real network call.

The synthetic fixture is a 4-team results grid, well below the ~20-team size
Wikipedia's real pages use. `_looks_like_results_grid` and `_find_grid_table`
both gate on that real-world size (>=10x10, >=15 distinct header texts) to
disambiguate the right table among many on a real page — irrelevant here,
where there's exactly one table and we're testing the extraction logic
itself, so those two size gates are bypassed via monkeypatch.
"""

from io import StringIO

import pandas as pd

from app.ingestion import wikipedia_scraper

SYNTHETIC_GRID_HTML = """
<table>
<tr>
  <th>Home \\ Away</th>
  <th><a title="Team Alpha">TMA</a></th>
  <th><a title="Team Beta">TMB</a></th>
  <th><a title="Team Gamma">TMG</a></th>
  <th><a title="Team Delta">TMD</a></th>
</tr>
<tr>
  <th><a title="Team Alpha">Team Alpha</a></th>
  <td>&mdash;</td><td>2&ndash;1</td><td>1&ndash;1</td><td>abd.</td>
</tr>
<tr>
  <th><a title="Team Beta">Team Beta</a></th>
  <td>0&ndash;0</td><td>&mdash;</td><td>3&ndash;2</td><td>1&ndash;0</td>
</tr>
<tr>
  <th><a title="Team Gamma">Team Gamma</a></th>
  <td>2&ndash;2</td><td>1&ndash;3</td><td>&mdash;</td><td>0&ndash;1</td>
</tr>
<tr>
  <th><a title="Team Delta">Team Delta</a></th>
  <td>1&ndash;1</td><td>2&ndash;0</td><td>3&ndash;1</td><td>&mdash;</td>
</tr>
</table>
"""


def _install_fakes(monkeypatch):
    def fake_fetch_page(title):
        return SYNTHETIC_GRID_HTML, pd.read_html(StringIO(SYNTHETIC_GRID_HTML))

    monkeypatch.setattr(wikipedia_scraper, "_fetch_page", fake_fetch_page)
    # Real-page size heuristics don't apply to a 4-team synthetic fixture —
    # bypass them so we're testing extraction, not table disambiguation.
    monkeypatch.setattr(wikipedia_scraper, "_looks_like_results_grid", lambda df: True)
    monkeypatch.setattr(wikipedia_scraper, "_find_grid_table", lambda soup, anchor: soup.find("table"))


def test_extracts_every_match_not_just_one_teams(monkeypatch):
    _install_fakes(monkeypatch)

    matches = wikipedia_scraper.scrape_serie_a_season("2023-2024")

    # 4 teams * 3 opponents = 12 off-diagonal cells, minus 1 unparseable
    # annotation ("abd.") = 11 valid matches.
    assert len(matches) == 11

    teams_involved = {m["home_team"] for m in matches} | {m["away_team"] for m in matches}
    assert teams_involved == {"Team Alpha", "Team Beta", "Team Gamma", "Team Delta"}

    # Every match date is the same season-start placeholder (documented limitation).
    assert all(m["match_date"].year == 2023 for m in matches)


def test_resolves_full_names_via_a_title_map_not_raw_codes(monkeypatch):
    _install_fakes(monkeypatch)

    matches = wikipedia_scraper.scrape_serie_a_season("2023-2024")

    beta_vs_alpha = next(m for m in matches if m["home_team"] == "Team Beta" and m["away_team"] == "Team Alpha")
    assert beta_vs_alpha["home_goals"] == 0
    assert beta_vs_alpha["away_goals"] == 0

    # Never a raw column code like "TMA" leaking through unresolved.
    assert not any(name in ("TMA", "TMB", "TMG", "TMD") for m in matches for name in (m["home_team"], m["away_team"]))


def test_unparseable_annotation_is_skipped_not_crashed(monkeypatch):
    _install_fakes(monkeypatch)

    matches = wikipedia_scraper.scrape_serie_a_season("2023-2024")

    alpha_vs_delta = [m for m in matches if m["home_team"] == "Team Alpha" and m["away_team"] == "Team Delta"]
    assert alpha_vs_delta == []  # the "abd." cell never became a match


def test_shortfall_is_logged_as_warning(monkeypatch, caplog):
    _install_fakes(monkeypatch)

    with caplog.at_level("WARNING", logger="app.ingestion.wikipedia_scraper"):
        matches = wikipedia_scraper.scrape_serie_a_season("2023-2024")

    assert len(matches) == 11
    assert any("Extracted 11/12 expected matches" in record.message for record in caplog.records)
