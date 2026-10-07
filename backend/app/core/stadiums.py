"""Static reference data: stadium name/city/coordinates for the clubs seen in
the ingested dataset (Serie A clubs from the seasons covered by the data).
This doesn't change often enough to warrant a DB table or an ingestion step —
a plain dict is simpler and doesn't depend on any external service being up.

Coordinates are approximate (stadium/city center), good enough for a
travel-time estimate — not survey-grade precision.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class StadiumInfo:
    name: str
    city: str
    lat: float
    lon: float


STADIUMS: dict[str, StadiumInfo] = {
    "Atalanta BC": StadiumInfo("Gewiss Stadium", "Bergamo", 45.7089, 9.6807),
    "AC Milan": StadiumInfo("San Siro", "Milano", 45.4781, 9.1240),
    "Inter Milan": StadiumInfo("San Siro", "Milano", 45.4781, 9.1240),
    "AS Roma": StadiumInfo("Stadio Olimpico", "Roma", 41.9341, 12.4547),
    "SS Lazio": StadiumInfo("Stadio Olimpico", "Roma", 41.9341, 12.4547),
    "ACF Fiorentina": StadiumInfo("Stadio Artemio Franchi", "Firenze", 43.7809, 11.2822),
    "Bologna FC 1909": StadiumInfo("Stadio Renato Dall'Ara", "Bologna", 44.4923, 11.3096),
    "Cagliari Calcio": StadiumInfo("Unipol Domus", "Cagliari", 39.2238, 9.1217),
    "Empoli FC": StadiumInfo("Stadio Carlo Castellani", "Empoli", 43.7222, 10.9385),
    "Genoa CFC": StadiumInfo("Stadio Luigi Ferraris", "Genova", 44.4163, 8.9526),
    "UC Sampdoria": StadiumInfo("Stadio Luigi Ferraris", "Genova", 44.4163, 8.9526),
    "Hellas Verona FC": StadiumInfo("Stadio Marcantonio Bentegodi", "Verona", 45.4352, 10.9686),
    "AC Monza": StadiumInfo("U-Power Stadium", "Monza", 45.5845, 9.2996),
    "SSC Napoli": StadiumInfo("Stadio Diego Armando Maradona", "Napoli", 40.8279, 14.1930),
    "Torino FC": StadiumInfo("Stadio Olimpico Grande Torino", "Torino", 45.0420, 7.6498),
    "Udinese Calcio": StadiumInfo("Bluenergy Stadium", "Udine", 46.0803, 13.2035),
    "US Sassuolo Calcio": StadiumInfo("Mapei Stadium", "Reggio Emilia", 44.6926, 10.6740),
    "US Lecce": StadiumInfo("Stadio Via del Mare", "Lecce", 40.3572, 18.1631),
    "US Salernitana 1919": StadiumInfo("Stadio Arechi", "Salerno", 40.6633, 14.7936),
    "Frosinone Calcio": StadiumInfo("Stadio Benito Stirpe", "Frosinone", 41.6297, 13.3574),
    "Spezia Calcio": StadiumInfo("Stadio Alberto Picco", "La Spezia", 44.1044, 9.8385),
    "Venezia FC": StadiumInfo("Stadio Pier Luigi Penzo", "Venezia", 45.4198, 12.3517),
    "Benevento Calcio": StadiumInfo("Stadio Ciro Vigorito", "Benevento", 41.1298, 14.7826),
    "Brescia Calcio": StadiumInfo("Stadio Mario Rigamonti", "Brescia", 45.5411, 10.2361),
    "Parma Calcio 1913": StadiumInfo("Stadio Ennio Tardini", "Parma", 44.7897, 10.3378),
    "FC Crotone": StadiumInfo("Stadio Ezio Scida", "Crotone", 39.0847, 17.1128),
    "SPAL": StadiumInfo("Stadio Paolo Mazza", "Ferrara", 44.8228, 11.6317),
    "US Cremonese": StadiumInfo("Stadio Giovanni Zini", "Cremona", 45.1275, 10.0284),
    "Como 1907": StadiumInfo("Stadio Giuseppe Sinigaglia", "Como", 45.8081, 9.0852),
}
