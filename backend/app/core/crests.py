"""Static reference data: team crest image URLs, keyed by the same canonical
names used throughout this codebase (see app.core.teams / app.core.stadiums).
Like stadiums.py, this doesn't change often enough to warrant a DB table or
an ingestion step.

URLs are football-data.org's own crest CDN (verified against a real,
read-only call to GET /v4/competitions/SA/teams — not guessed), one per
club that appeared in that response for the 2026-27 Serie A season.
Historic/relegated clubs not in the current season's roster (Empoli,
Cremonese, FC Crotone, Salernitana, Spezia, Hellas Verona, Benevento,
Brescia, SPAL, Sampdoria) have no entry here — a lookup miss is expected
and handled gracefully by callers (no image shown), not an error.
"""

CRESTS: dict[str, str] = {
    "Juventus FC": "https://crests.football-data.org/109.png",
    "AC Milan": "https://crests.football-data.org/98.png",
    "ACF Fiorentina": "https://crests.football-data.org/99.png",
    "AS Roma": "https://crests.football-data.org/100.png",
    "Atalanta BC": "https://crests.football-data.org/102.png",
    "Bologna FC 1909": "https://crests.football-data.org/103.png",
    "Cagliari Calcio": "https://crests.football-data.org/104.png",
    "Genoa CFC": "https://crests.football-data.org/107.png",
    "Inter Milan": "https://crests.football-data.org/108.png",
    "SS Lazio": "https://crests.football-data.org/110.png",
    "Parma Calcio 1913": "https://crests.football-data.org/112.png",
    "SSC Napoli": "https://crests.football-data.org/113.png",
    "Udinese Calcio": "https://crests.football-data.org/115.png",
    "Venezia FC": "https://crests.football-data.org/454.png",
    "Frosinone Calcio": "https://crests.football-data.org/470.png",
    "US Sassuolo Calcio": "https://crests.football-data.org/471.png",
    "Torino FC": "https://crests.football-data.org/586.png",
    "US Lecce": "https://crests.football-data.org/5890.png",
    "AC Monza": "https://crests.football-data.org/5911.png",
    "Como 1907": "https://crests.football-data.org/7397.png",
}
