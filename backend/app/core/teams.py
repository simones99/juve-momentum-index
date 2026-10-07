"""Team name alias resolution: maps known alternate spellings of a club
(short names, football-data.org's official names, common colloquial names)
to the canonical name already used throughout this codebase.

The canonical names are NOT invented here — they are exactly the 29 keys
already in `app.core.stadiums.STADIUMS`, which are the period-stripped
Wikipedia names already stored in the live dataset and used for Elo/
head-to-head matching and for Trasferte's stadium lookup. Changing a
canonical spelling here without also updating stadiums.py (and re-ingesting)
would silently break that matching.

This map is necessarily incomplete: it's built from general knowledge of
common club-name variants, not from a real football-data.org response (no
API key was configured when it was first written). Once a key
is available, run `scripts/check_team_names.py` against a real ingestion to
find any unmapped names and extend ALIASES below.

Lookup is case-insensitive and expects the input to already have had periods
stripped (see normalize.py's `_strip_periods`, applied before this is
called) — aliases here are written without periods for that reason.
"""

# alias (lowercase, no periods) -> canonical name (matches app.core.stadiums.STADIUMS keys)
ALIASES: dict[str, str] = {
    # Inter Milan
    "inter": "Inter Milan",
    "internazionale": "Inter Milan",
    "fc internazionale milano": "Inter Milan",
    "inter milano": "Inter Milan",
    # AC Milan
    "milan": "AC Milan",
    "ac milan": "AC Milan",
    # AS Roma
    "roma": "AS Roma",
    "as roma": "AS Roma",
    # SS Lazio
    "lazio": "SS Lazio",
    "ss lazio": "SS Lazio",
    # SSC Napoli
    "napoli": "SSC Napoli",
    "ssc napoli": "SSC Napoli",
    # ACF Fiorentina
    "fiorentina": "ACF Fiorentina",
    "acf fiorentina": "ACF Fiorentina",
    # Bologna FC 1909
    "bologna": "Bologna FC 1909",
    "bologna fc": "Bologna FC 1909",
    "bologna fc 1909": "Bologna FC 1909",
    # Torino FC
    "torino": "Torino FC",
    "torino fc": "Torino FC",
    # Genoa CFC
    "genoa": "Genoa CFC",
    "genoa cfc": "Genoa CFC",
    # Udinese Calcio
    "udinese": "Udinese Calcio",
    "udinese calcio": "Udinese Calcio",
    # US Sassuolo Calcio
    "sassuolo": "US Sassuolo Calcio",
    "us sassuolo calcio": "US Sassuolo Calcio",
    "sassuolo calcio": "US Sassuolo Calcio",
    # Hellas Verona FC
    "verona": "Hellas Verona FC",
    "hellas verona": "Hellas Verona FC",
    "hellas verona fc": "Hellas Verona FC",
    # Cagliari Calcio
    "cagliari": "Cagliari Calcio",
    "cagliari calcio": "Cagliari Calcio",
    # US Lecce
    "lecce": "US Lecce",
    "us lecce": "US Lecce",
    # Empoli FC
    "empoli": "Empoli FC",
    "empoli fc": "Empoli FC",
    # AC Monza
    "monza": "AC Monza",
    "ac monza": "AC Monza",
    # UC Sampdoria
    "sampdoria": "UC Sampdoria",
    "uc sampdoria": "UC Sampdoria",
    # Parma Calcio 1913
    "parma": "Parma Calcio 1913",
    "parma calcio": "Parma Calcio 1913",
    "parma calcio 1913": "Parma Calcio 1913",
    # US Salernitana 1919
    "salernitana": "US Salernitana 1919",
    "us salernitana 1919": "US Salernitana 1919",
    # Frosinone Calcio
    "frosinone": "Frosinone Calcio",
    "frosinone calcio": "Frosinone Calcio",
    # Spezia Calcio
    "spezia": "Spezia Calcio",
    "spezia calcio": "Spezia Calcio",
    # Venezia FC
    "venezia": "Venezia FC",
    "venezia fc": "Venezia FC",
    # US Cremonese
    "cremonese": "US Cremonese",
    "us cremonese": "US Cremonese",
    # Como 1907
    "como": "Como 1907",
    "como 1907": "Como 1907",
    # Atalanta BC
    "atalanta": "Atalanta BC",
    "atalanta bc": "Atalanta BC",
    # Benevento Calcio
    "benevento": "Benevento Calcio",
    "benevento calcio": "Benevento Calcio",
    # Brescia Calcio
    "brescia": "Brescia Calcio",
    "brescia calcio": "Brescia Calcio",
    # FC Crotone
    "crotone": "FC Crotone",
    "fc crotone": "FC Crotone",
    # SPAL
    "spal": "SPAL",
    "spal 2013": "SPAL",
}


def resolve_alias(name: str) -> str | None:
    """Returns the canonical name for a known alias, or None if `name` isn't
    recognized (caller should fall back to the input as-is)."""
    return ALIASES.get(name.strip().lower())
