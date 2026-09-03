# Juve Momentum Index

![CI](https://github.com/simones99/juve-momentum-index/actions/workflows/ci.yml/badge.svg)

Un **Momentum Index** per la Juventus — un punteggio 0-100 che combina Elo e forma
recente — esposto in una dashboard con andamento nel tempo, storico partite e una
feature **Match Brief**: un recap pre/post-partita generato da template dati e,
quando configurato, arricchito da un LLM via [OpenRouter](https://openrouter.ai/).

- **Demo live**: `<link Vercel qui dopo il deploy>`
- **API (Swagger)**: `<link Render qui dopo il deploy>/docs`

![Overview screenshot placeholder](docs/screenshots/overview.png)

## Cosa fa

- Calcola un rating **Elo** partita per partita per la Juventus (Serie A + Champions
  League, ultime stagioni), con home advantage e K-factor configurabili.
- Combina l'Elo normalizzato con la forma recente (punti e differenza reti su
  finestre di 5/10 partite) in un **Momentum Index** 0-100.
- Genera un **brief testuale** pre-partita (forma recente, trend Elo, precedenti
  contro l'avversario, **probabilità di vittoria/pareggio/sconfitta**) o post-partita
  (confronto tra la prestazione e la media recente, più l'esito che il modello
  avrebbe previsto), con arricchimento opzionale via LLM (OpenRouter) e fallback
  automatico a testo template se l'LLM non è disponibile.
- Dashboard Next.js con 4 viste: Overview, Momentum Details, Matches, Match Brief.

## Architettura

```
Next.js (Vercel)  ──HTTP──▶  FastAPI (Render, Docker)  ──▶  Postgres (Neon)
                                     │
                                     ├─ ingestion: football-data.org (primaria)
                                     │             + fallback scraping Wikipedia
                                     └─ brief: template Python + OpenRouter (opzionale)
```

- **Backend**: FastAPI + SQLAlchemy + Alembic, Python 3.11+.
- **Frontend**: Next.js (App Router) + TypeScript + Recharts.
- **Database**: Postgres (stesso engine in dev e produzione).
- **Deploy**: Vercel (frontend) + Render (backend, da Dockerfile) + Neon (Postgres).

## Setup locale — senza Docker

Richiede Python 3.11+, Node 20+, e un Postgres locale raggiungibile (es. via
Homebrew: `brew install postgresql@16 && brew services start postgresql@16`, poi
crea un DB/utente `juventum`).

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # compila almeno DATABASE_URL
alembic upgrade head
python -m app.ingestion.ingest --seasons 2022-2023,2023-2024,2024-2025
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Apri `http://localhost:3000`.

## Setup locale — con Docker

```bash
docker compose build
docker compose run --rm ingest      # scarica/aggiorna i dati la prima volta
docker compose up backend frontend  # dashboard su http://localhost:3000, API su :8000
```

Il database Postgres gira come servizio `db` nello stesso `docker-compose.yml`,
con un volume persistente (`pgdata`) così i dati sopravvivono al rebuild.

Per aggiornare i dati periodicamente: `docker compose run --rm ingest`.

### Risolvere `JUVENTUS_TEAM_ID` (una tantum)

L'ingestion da football-data.org richiede l'id numerico della Juventus:

```bash
cd backend && python scripts/resolve_team_id.py
```

Copia il valore stampato in `JUVENTUS_TEAM_ID` nel tuo `.env` (o nelle variabili
d'ambiente Render).

## Deploy in produzione

1. **Neon**: crea un progetto Postgres, usa la connection string *pooled* per
   `DATABASE_URL` del backend, quella diretta per lanciare le migration Alembic.
2. **Render**: nuovo Web Service da Docker, root directory `backend/`, health
   check `/healthz`. Configura `DATABASE_URL`, `FOOTBALL_DATA_API_KEY`,
   `JUVENTUS_TEAM_ID`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`,
   `ENABLE_LLM_BRIEF`, `CORS_ORIGINS`, `ADMIN_TOKEN`. Dopo il primo deploy lancia
   l'ingestion una volta via Render Shell.
3. **Vercel**: importa `frontend/` come root directory, imposta
   `NEXT_PUBLIC_API_BASE_URL` sull'URL pubblico del backend Render (richiede un
   redeploy se cambiata, perché è compilata a build time).

## Fonti dati

- [football-data.org](https://www.football-data.org/) (free tier, 10
  richieste/minuto) — fonte primaria per Serie A e Champions League.
- Wikipedia (pagine "20XX-YY Serie A") — fallback automatico solo per Serie A,
  usato se l'API fallisce o esaurisce la quota per una stagione.

## Limiti noti

- **Elo semplificato**: il dataset contiene solo partite della Juventus, quindi
  non è un vero Elo storico multi-squadra — ogni avversario riparte da 1500 alla
  prima apparizione nel dataset.
- **Probabilità di vittoria, backtestate ma non "calibrate" in senso stretto**:
  derivano dall'expected score Elo più un modello di pareggio a campana
  (`features/win_probability.py`). Le costanti sono state validate con
  `scripts/backtest_win_probability.py` tramite cross-validation
  leave-one-season-out su 6 stagioni reali (2019-20 → 2024-25, 228 partite),
  valutando log loss / Brier score / accuracy contro una baseline uniforme e
  una baseline "frequenze storiche". Risultato: il modello batte entrambe le
  baseline in modo consistente ma con margine modesto (log loss medio 0.989
  vs 0.995 della baseline a frequenze) — un margine reale ma piccolo su un
  dataset di sole 228 partite di un unico club dominante, non una
  dimostrazione di forte potere predittivo.
- **Rate limit football-data.org**: 10 richieste/minuto sul piano gratuito; il
  client applica backoff automatico.
- **Cold start Render (piano free)**: il backend può impiegare 30-60s a
  rispondere dopo un periodo di inattività.
- **OpenRouter**: se la chiave non è configurata, i crediti sono esauriti o la
  richiesta va in timeout, il Match Brief torna automaticamente al testo
  template — l'endpoint non fallisce mai per questo motivo.
- **Fallback Wikipedia**: non copre la Champions League (formato cambiato tra le
  stagioni) e non ha date puntuali per singola partita (usa una data
  placeholder di inizio stagione) — è un fallback secondario, non il percorso
  critico.

## Test

```bash
cd backend
pytest -q
```

I test di calcolo (Elo, rolling stats, Momentum Index) sono puri e non richiedono
un database. I test API richiedono un Postgres raggiungibile: in locale creano
automaticamente un database `<nome>_test` separato da quello di sviluppo (per non
sovrascrivere i tuoi dati), in CI usano il servizio Postgres del workflow.

### Backtest del modello di probabilità

```bash
cd backend
python -m app.ingestion.ingest --seasons 2019-2020,2020-2021,2021-2022,2022-2023,2023-2024,2024-2025
python scripts/backtest_win_probability.py
```

Valuta `features/win_probability.py` con metodologia da modello ML (holdout
cronologico + cross-validation leave-one-season-out, log loss/Brier/accuracy
contro baseline uniforme e a frequenze storiche) e riporta anche una tabella
di calibrazione. Vedi il docstring dello script e la nota in "Limiti noti".

## Licenza

MIT — vedi [LICENSE](LICENSE). Progetto personale, non affiliato alla Juventus FC;
i dati sono indicativi e provengono da fonti pubbliche.
