# Dati vivi e messa in produzione — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ogni pagina mostra la stagione in corso con date/orari/stadi veri, i dati si aggiornano da soli senza il Mac acceso, e l'app ha un URL da mandare agli amici.

**Architecture:** Nessun nuovo servizio a pagamento. Il refresh giornaliero si sposta da un job `launchd` locale a un workflow GitHub Actions schedulato che gira sul codice di `main`; il live poll resta un semplice `POST /admin/poll-live` chiamato ora da un servizio cron esterno (cron-job.org) invece che dal Mac. Una nuova tabella `ingest_runs` rende visibile la freschezza dei dati in `/healthz` e nel footer. Deploy su Neon (Postgres) → Render (backend, Docker) → Vercel (frontend), tutti free tier.

**Tech Stack:** FastAPI + SQLAlchemy + Alembic (backend), Next.js App Router + TypeScript (frontend), GitHub Actions (cron cloud), Postgres.

**Spec:** `docs/analisi-prodotto-2026-09-09.md`, sezione "1. Dati vivi e messa in produzione" (gap G1-G7).

## Global Constraints

- Solo free tier: Render (spin-down), Neon, football-data.org (10 req/min, finestra ~4 stagioni), OSRM demo, Nominatim (1 req/s). Nessuna spesa fissa.
- Nessun account utente; identità = cookie `device_id`. Non rilevante per questo piano.
- Nessuna nuova libreria UI, nessun nuovo servizio a pagamento.
- Ogni euristica/dato approssimato resta dichiarato esplicitamente in UI (pattern `is_estimated`/`is_approximate` già usato in `AwayFixtureOut`/`LiveMatchOut`).
- Le funzionalità nuove seguono i pattern esistenti: modulo puro in `features/` o `ingestion/`, endpoint sottile in `api/routes/`, schema Pydantic in `schemas/`, migrazione Alembic, test per lo strato puro e per l'API.
- Verificare le API Next 16 in `frontend/node_modules/next/dist/docs/` prima di scrivere codice frontend (regola in `frontend/AGENTS.md`).
- Italiano prima, inglese mantenuto — ogni testo utente va in entrambe le lingue in `frontend/lib/i18n/dictionaries.ts`.

---

## File Structure

**Backend — codice:**
- Modify: `backend/app/schemas/match.py` — nuovo campo `is_approximate_date` su `MatchOut`.
- Modify: `backend/app/api/routes/matches.py` — valorizza `is_approximate_date` in `match_to_out`.
- Create: `backend/app/models/ingest_run.py` — modello `IngestRun`.
- Modify: `backend/app/models/__init__.py` — registra `IngestRun`.
- Create: `backend/alembic/versions/<hash>_add_ingest_runs.py` — tabella `ingest_runs`.
- Modify: `backend/app/ingestion/repository.py` — funzione `record_ingest_run`.
- Modify: `backend/app/ingestion/ingest.py` — `update_matches` traccia e registra il run.
- Modify: `backend/app/api/routes/health.py` — `/healthz` espone `last_successful_ingest_at`.
- Modify: `scripts/scheduled_ingest.sh` — `docker compose run --build --rm ingest`.
- Create: `.github/workflows/scheduled-ingest.yml` — cron cloud giornaliero.

**Backend — test:**
- Modify: `backend/tests/test_api_matches.py` — badge data approssimata.
- Modify: `backend/tests/test_ingest.py` — `record_ingest_run` chiamato da `update_matches`.
- Create: `backend/tests/test_health.py` — `/healthz` con e senza ingest riuscito.

**Frontend:**
- Modify: `frontend/lib/types.ts` — `MatchOut.is_approximate_date`, nuovo tipo `HealthzResponse`.
- Modify: `frontend/lib/api.ts` — `getHealthz()`.
- Modify: `frontend/lib/i18n/dictionaries.ts` — chiavi `matches.table.approximateDate` e `footerUpdatedAt` (IT+EN, interfaccia + entrambi i dizionari).
- Modify: `frontend/components/MatchTable.tsx` — badge "Data approssimata".
- Modify: `frontend/app/globals.css` — classe `.badge--approx`.
- Modify: `frontend/app/layout.tsx` — footer con orario ultimo aggiornamento.

**Docs:**
- Modify: `README.md` — nota su DB di sviluppo unico, sezione cron cloud, `docs/backtest.md` (sezione finale dopo il rerun in Task 9).

---

### Task 1: Fix cron locale + DB di sviluppo unico

**Files:**
- Modify: `scripts/scheduled_ingest.sh:47`
- Modify: `README.md` (sezione "Setup locale — con Docker")

**Interfaces:** nessuna (script + doc).

- [ ] **Step 1: `--build` nello script di ingest schedulato**

In `scripts/scheduled_ingest.sh`, riga 47:

```bash
docker compose run --rm ingest
```

diventa:

```bash
docker compose run --build --rm ingest
```

Così ogni run locale ricostruisce l'immagine `ingest` sul codice attuale invece di girare su un'immagine Docker stantia (causa nota del 403 non gestito in G3 dell'analisi prodotto).

- [ ] **Step 2: dichiarare un solo Postgres di sviluppo nel README**

In `README.md`, subito dopo la sezione "Setup locale — con Docker" (dopo la riga che spiega il volume `pgdata`), aggiungere:

```markdown
> **Un solo Postgres alla volta.** Sia il Postgres Homebrew (`localhost:5432` di
> sistema) sia il container `db` di `docker-compose.yml` ascoltano sulla stessa
> porta 5432: se sono entrambi attivi, quale dei due risponde dipende da quale è
> partito per primo, e i due database divergono silenziosamente. Usa il
> container `db` come fonte di verità (è quello scritto dal job di ingestion in
> `docker compose run --rm ingest` e dal workflow GitHub Actions — vedi sotto):
> se lavori senza Docker, ferma `brew services stop postgresql@16` prima di
> avviare `docker compose up`.
```

- [ ] **Step 3: commit**

```bash
git add scripts/scheduled_ingest.sh README.md
git commit -m "fix: rebuild ingest image on scheduled runs, document single dev DB"
```

---

### Task 2: Backend — flag "data approssimata" per le partite da Wikipedia

**Files:**
- Modify: `backend/app/schemas/match.py`
- Modify: `backend/app/api/routes/matches.py`
- Test: `backend/tests/test_api_matches.py`

**Interfaces:**
- Produces: `MatchOut.is_approximate_date: bool` — `true` quando `match.source == SOURCE_WIKIPEDIA` (data placeholder di inizio stagione, non la data reale della partita).

- [ ] **Step 1: scrivere il test che fallisce**

Aggiungere in fondo a `backend/tests/test_api_matches.py`:

```python
from app.core.constants import SOURCE_WIKIPEDIA


def test_list_matches_flags_wikipedia_sourced_matches_as_approximate(client, db):
    db.add(_make_match(external_id="fd-1", source=SOURCE_FOOTBALL_DATA))
    db.add(_make_match(external_id="wiki-1", source=SOURCE_WIKIPEDIA, away_team="Milan"))
    db.commit()

    response = client.get("/api/v1/matches")
    by_source = {m["away_team"]: m["is_approximate_date"] for m in response.json()["items"]}

    assert by_source["Inter"] is False
    assert by_source["Milan"] is True
```

(Il file importa già `SOURCE_FOOTBALL_DATA` in cima; aggiungi `SOURCE_WIKIPEDIA` accanto, oppure nell'import esistente `from app.core.constants import COMPETITION_SERIE_A, SOURCE_FOOTBALL_DATA, TEAM_NAME` aggiungi `SOURCE_WIKIPEDIA`.)

- [ ] **Step 2: eseguire il test e verificare che fallisca**

Run: `cd backend && pytest tests/test_api_matches.py::test_list_matches_flags_wikipedia_sourced_matches_as_approximate -v`
Expected: FAIL — `KeyError: 'is_approximate_date'` (il campo non esiste ancora nella risposta).

- [ ] **Step 3: aggiungere il campo allo schema**

In `backend/app/schemas/match.py`, in `MatchOut` dopo il campo `status: str`:

```python
    status: str
    result: str | None = None  # W/D/L from Juventus' perspective, None if not yet played
    is_approximate_date: bool = False
```

- [ ] **Step 4: valorizzarlo in `match_to_out`**

In `backend/app/api/routes/matches.py`, aggiungere `SOURCE_WIKIPEDIA` all'import esistente:

```python
from app.core.constants import LIVE_MATCH_STATUSES, MATCH_STATUS_FINISHED, SOURCE_WIKIPEDIA, TEAM_NAME, UPCOMING_MATCH_STATUSES
```

e in `match_to_out`, dopo `status=m.status,`:

```python
    return MatchOut(
        id=m.id,
        season=m.season,
        competition=m.competition,
        competition_code=m.competition_code,
        match_date=m.match_date,
        home_team=m.home_team,
        away_team=m.away_team,
        home_goals=m.home_goals,
        away_goals=m.away_goals,
        venue=m.venue,
        status=m.status,
        result=compute_result(m),
        is_approximate_date=m.source == SOURCE_WIKIPEDIA,
    )
```

- [ ] **Step 5: eseguire il test e verificare che passi**

Run: `cd backend && pytest tests/test_api_matches.py -v`
Expected: PASS (tutti i test del file, non solo quello nuovo — verifica che non hai rotto gli esistenti).

- [ ] **Step 6: commit**

```bash
git add backend/app/schemas/match.py backend/app/api/routes/matches.py backend/tests/test_api_matches.py
git commit -m "feat: flag wikipedia-sourced matches with approximate placeholder dates"
```

---

### Task 3: Frontend — badge "Data approssimata" nella tabella partite

**Files:**
- Modify: `frontend/lib/types.ts`
- Modify: `frontend/lib/i18n/dictionaries.ts`
- Modify: `frontend/components/MatchTable.tsx`
- Modify: `frontend/app/globals.css`

**Interfaces:**
- Consumes: `MatchOut.is_approximate_date` (Task 2).
- Produces: nessuna nuova interfaccia consumata da altri task.

- [ ] **Step 1: aggiungere il campo al tipo `MatchOut`**

In `frontend/lib/types.ts`, dentro `MatchOut` dopo `result: ResultLetter | null;`:

```ts
export interface MatchOut {
  id: number;
  season: string;
  competition: string;
  competition_code: string;
  match_date: string;
  home_team: string;
  away_team: string;
  home_goals: number | null;
  away_goals: number | null;
  venue: string | null;
  status: string;
  result: ResultLetter | null;
  is_approximate_date: boolean;
}
```

- [ ] **Step 2: aggiungere le chiavi i18n**

In `frontend/lib/i18n/dictionaries.ts`, nell'interfaccia `Dictionary` (verso riga 68-75), dentro `matches.table`:

```ts
    table: {
      date: string;
      competition: string;
      home: string;
      away: string;
      result: string;
      outcome: string;
      approximateDate: string;
    };
```

Nel dizionario italiano (riga ~239-246):

```ts
      table: {
        date: "Data",
        competition: "Competizione",
        home: "Casa",
        away: "Trasferta",
        result: "Risultato",
        outcome: "Esito",
        approximateDate: "Data approssimata",
      },
```

Nel dizionario inglese (riga ~410-417):

```ts
      table: {
        date: "Date",
        competition: "Competition",
        home: "Home",
        away: "Away",
        result: "Score",
        outcome: "Outcome",
        approximateDate: "Approximate date",
      },
```

- [ ] **Step 3: badge CSS**

In `frontend/app/globals.css`, dopo la regola `.badge--template` (circa riga 444):

```css
.badge--approx {
  background: rgba(205, 176, 121, 0.12);
  border: 1px solid var(--accent-border);
  color: var(--text-muted);
  font-weight: 600;
  text-transform: none;
}
```

- [ ] **Step 4: renderizzare il badge nella tabella**

In `frontend/components/MatchTable.tsx`, cella data (dentro `<tbody>`, `<td>{formatDate(...)}</td>`):

```tsx
            <td>
              {formatDate(m.match_date, locale)}
              {m.is_approximate_date && (
                <span className="badge badge--approx" style={{ marginLeft: 6 }} title={dict.matches.table.approximateDate}>
                  {dict.matches.table.approximateDate}
                </span>
              )}
            </td>
```

- [ ] **Step 5: verifica tipo/build**

Run: `cd frontend && npm run build`
Expected: build passa senza errori TypeScript (verifica che `dict.matches.table.approximateDate` e `MatchOut.is_approximate_date` siano coerenti in tutto il codice).

- [ ] **Step 6: verifica visiva**

Avviare `npm run dev`, aprire `/matches`, confermare che le righe con stagioni Wikipedia (source non football-data) mostrano il badge accanto alla data e che quelle da football-data.org no.

- [ ] **Step 7: commit**

```bash
git add frontend/lib/types.ts frontend/lib/i18n/dictionaries.ts frontend/components/MatchTable.tsx frontend/app/globals.css
git commit -m "feat: show approximate-date badge for wikipedia-sourced matches"
```

---

### Task 4: Backend — tabella `ingest_runs`

**Files:**
- Create: `backend/app/models/ingest_run.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/alembic/versions/<hash>_add_ingest_runs.py`

**Interfaces:**
- Produces: modello `IngestRun` con colonne `id, started_at, finished_at, status, matches_upserted, source_summary` — usato da Task 5 (scrittura) e Task 6 (lettura in `/healthz`).

- [ ] **Step 1: creare il modello**

`backend/app/models/ingest_run.py`:

```python
"""Tracks each ingestion run so the app can show data freshness (see
/healthz and the site footer) instead of leaving staleness invisible.
"""

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class IngestRun(Base):
    __tablename__ = "ingest_runs"
    __table_args__ = (Index("ix_ingest_runs_finished_at", "finished_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    matches_upserted: Mapped[int] = mapped_column(Integer, nullable=False)
    source_summary: Mapped[str] = mapped_column(String(256), nullable=False)
```

- [ ] **Step 2: registrarlo in `app/models/__init__.py`**

```python
from app.models.elo_rating import EloRating
from app.models.ingest_run import IngestRun
from app.models.juve_momentum import JuveMomentum
from app.models.match import Match
from app.models.prediction import Prediction
from app.models.push_subscription import PushSubscription

__all__ = ["Match", "EloRating", "JuveMomentum", "PushSubscription", "Prediction", "IngestRun"]
```

- [ ] **Step 3: generare la migrazione**

Run (da `backend/`, con un Postgres locale raggiungibile):

```bash
cd backend
alembic revision -m "add ingest runs"
```

Questo crea `backend/alembic/versions/<hash>_add_ingest_runs.py` con `down_revision` già impostato automaticamente su `'ba3da1269a3e'` (l'attuale head — verificabile con `alembic heads`). Sostituire il corpo di `upgrade()`/`downgrade()` generato con:

```python
def upgrade() -> None:
    op.create_table(
        "ingest_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("matches_upserted", sa.Integer(), nullable=False),
        sa.Column("source_summary", sa.String(length=256), nullable=False),
    )
    op.create_index("ix_ingest_runs_finished_at", "ingest_runs", ["finished_at"])


def downgrade() -> None:
    op.drop_index("ix_ingest_runs_finished_at", table_name="ingest_runs")
    op.drop_table("ingest_runs")
```

- [ ] **Step 4: applicare la migrazione e verificare**

Run: `cd backend && alembic upgrade head`
Expected: nessun errore; `psql` (o `docker compose exec db psql -U juventum -d juventum`) mostra la tabella con `\dt ingest_runs`.

- [ ] **Step 5: lint**

Run: `cd backend && ruff check app scripts`
Expected: nessun errore.

- [ ] **Step 6: commit**

```bash
git add backend/app/models/ingest_run.py backend/app/models/__init__.py backend/alembic/versions/*_add_ingest_runs.py
git commit -m "feat: add ingest_runs table for data-freshness tracking"
```

---

### Task 5: Backend — `update_matches` registra ogni run

**Files:**
- Modify: `backend/app/ingestion/repository.py`
- Modify: `backend/app/ingestion/ingest.py`
- Test: `backend/tests/test_ingest.py`

**Interfaces:**
- Consumes: `IngestRun` (Task 4).
- Produces: `record_ingest_run(db, *, started_at, finished_at, status, matches_upserted, source_summary) -> IngestRun` in `app.ingestion.repository` — usato solo da `update_matches`.

- [ ] **Step 1: scrivere il test che fallisce**

Aggiungere in fondo a `backend/tests/test_ingest.py`:

```python
from app.models.ingest_run import IngestRun


def test_update_matches_records_a_successful_ingest_run(db, monkeypatch):
    monkeypatch.setattr("app.ingestion.ingest.SessionLocal", lambda: db)
    monkeypatch.setattr(db, "close", lambda: None)

    raw_matches = [
        _raw_match(1, "Juventus FC", "SSC Napoli", 2, 0, "2024-09-08T18:45:00Z"),
        _raw_match(2, "AC Milan", "Inter Milan", 1, 1, "2024-09-01T18:45:00Z"),
    ]
    monkeypatch.setattr(FootballDataClient, "get_competition_matches", lambda self, code, season: raw_matches)

    update_matches(seasons=["2024-2025"], competitions=[COMPETITION_SERIE_A])

    run = db.scalar(select(IngestRun).order_by(IngestRun.id.desc()))
    assert run is not None
    assert run.status == "success"
    assert run.matches_upserted == 2
    assert run.source_summary == "football-data:2"
    assert run.finished_at >= run.started_at
```

`_raw_match` e `select` sono già importati/definiti in cima al file (vedi i test esistenti che li usano); se `select` non è già importato, aggiungere `from sqlalchemy import select` all'inizio del file.

- [ ] **Step 2: eseguire il test e verificare che fallisca**

Run: `cd backend && pytest tests/test_ingest.py::test_update_matches_records_a_successful_ingest_run -v`
Expected: FAIL — `run is None` (nessuna riga in `ingest_runs`, la funzione non la scrive ancora).

- [ ] **Step 3: aggiungere `record_ingest_run` al repository**

In `backend/app/ingestion/repository.py`, aggiungere in cima l'import mancante e la funzione in fondo al file:

```python
from datetime import datetime
```

(accanto agli import esistenti `from sqlalchemy import delete, select` ecc.)

```python
from app.models.ingest_run import IngestRun
```

(accanto a `from app.models.match import Match`)

E in fondo al file:

```python
def record_ingest_run(
    db: Session,
    *,
    started_at: datetime,
    finished_at: datetime,
    status: str,
    matches_upserted: int,
    source_summary: str,
) -> IngestRun:
    run = IngestRun(
        started_at=started_at,
        finished_at=finished_at,
        status=status,
        matches_upserted=matches_upserted,
        source_summary=source_summary,
    )
    db.add(run)
    return run
```

- [ ] **Step 4: chiamarla da `update_matches`**

In `backend/app/ingestion/ingest.py`:

1. Aggiungere `SOURCE_FOOTBALL_DATA, SOURCE_WIKIPEDIA` all'import da `app.core.constants` (riga 21-27):

```python
from app.core.constants import (
    COMPETITION_SERIE_A,
    MATCH_STATUS_FINISHED,
    SOURCE_FOOTBALL_DATA,
    SOURCE_WIKIPEDIA,
    SUPPORTED_COMPETITIONS,
    TEAM_NAME,
    UPCOMING_MATCH_STATUSES,
)
```

2. Aggiungere `record_ingest_run` all'import da `app.ingestion.repository` (riga 32):

```python
from app.ingestion.repository import delete_wikipedia_rows_for_season, record_ingest_run, upsert_match
```

3. Sostituire l'intero corpo di `update_matches` (righe 183-224) con:

```python
def update_matches(seasons: list[str] | None = None, competitions: list[str] | None = None) -> None:
    """Downloads/updates match data for the requested seasons (the WHOLE
    competition, not just Juventus' fixtures) and persists it to the DB,
    then recomputes elo/momentum for the whole dataset."""
    settings = get_settings()
    seasons = seasons or default_seasons()
    competitions = competitions or SUPPORTED_COMPETITIONS

    db: Session = SessionLocal()
    started_at = datetime.now(timezone.utc)
    source_counts: dict[str, int] = {}
    try:
        client = FootballDataClient(api_key=settings.football_data_api_key)

        for season in seasons:
            for competition_code in competitions:
                try:
                    count = _ingest_competition_from_football_data(db, client, competition_code, season)
                    source_counts[SOURCE_FOOTBALL_DATA] = source_counts.get(SOURCE_FOOTBALL_DATA, 0) + count
                    logger.info(
                        "season %s %s: ingested %d matches from football-data.org",
                        season, competition_code, count,
                    )
                except FootballDataError as exc:
                    has_fallback = competition_code == COMPETITION_SERIE_A
                    logger.warning(
                        "season %s %s: football-data.org failed (%s)%s",
                        season, competition_code, exc,
                        "; falling back to Wikipedia" if has_fallback else " (no fallback for this competition)",
                    )
                    if has_fallback:
                        count = _ingest_season_from_wikipedia(db, season)
                        source_counts[SOURCE_WIKIPEDIA] = source_counts.get(SOURCE_WIKIPEDIA, 0) + count
                        logger.info("season %s: ingested %d matches from Wikipedia fallback", season, count)

        db.commit()

        recompute_all_derived(db)
        db.commit()
        logger.info("Recomputed elo_ratings and juve_momentum")

        _resolve_finished_predictions(db)
        _notify_brief_ready(db)
        _notify_momentum_swing(db)

        record_ingest_run(
            db,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            status="success",
            matches_upserted=sum(source_counts.values()),
            source_summary=", ".join(f"{k}:{v}" for k, v in sorted(source_counts.items())) or "none",
        )
        db.commit()
    finally:
        db.close()
```

- [ ] **Step 5: eseguire il test e verificare che passi**

Run: `cd backend && pytest tests/test_ingest.py -v`
Expected: PASS (tutti i test del file).

- [ ] **Step 6: suite completa**

Run: `cd backend && pytest -q`
Expected: PASS — verifica che non hai rotto `test_ingest_notifications.py`/`test_ingest_predictions.py`, che dipendono dallo stesso `update_matches`.

- [ ] **Step 7: commit**

```bash
git add backend/app/ingestion/repository.py backend/app/ingestion/ingest.py backend/tests/test_ingest.py
git commit -m "feat: record each ingest run in ingest_runs"
```

---

### Task 6: Backend — `/healthz` espone la freschezza dei dati

**Files:**
- Modify: `backend/app/api/routes/health.py`
- Test: `backend/tests/test_health.py` (nuovo)

**Interfaces:**
- Consumes: `IngestRun` (Task 4).
- Produces: `GET /healthz` → `{"status": "ok", "last_successful_ingest_at": str | None}` (ISO 8601) — consumato da Task 7 (frontend).

- [ ] **Step 1: scrivere il test che fallisce**

`backend/tests/test_health.py`:

```python
from datetime import datetime, timezone

from app.models.ingest_run import IngestRun


def test_healthz_reports_null_when_no_ingest_ever_ran(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "last_successful_ingest_at": None}


def test_healthz_reports_the_latest_successful_ingest_timestamp(client, db):
    finished = datetime(2026, 9, 9, 3, 12, tzinfo=timezone.utc)
    db.add(
        IngestRun(
            started_at=finished,
            finished_at=finished,
            status="success",
            matches_upserted=42,
            source_summary="football-data:42",
        )
    )
    db.commit()

    response = client.get("/healthz")

    assert response.json() == {"status": "ok", "last_successful_ingest_at": finished.isoformat()}
```

- [ ] **Step 2: eseguire il test e verificare che fallisca**

Run: `cd backend && pytest tests/test_health.py -v`
Expected: FAIL — la risposta oggi è solo `{"status": "ok"}`, senza `last_successful_ingest_at`.

- [ ] **Step 3: implementare**

`backend/app/api/routes/health.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.ingest_run import IngestRun

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz(db: Session = Depends(get_db)) -> dict:
    db.execute(text("SELECT 1"))
    last_successful = db.scalar(
        select(IngestRun.finished_at)
        .where(IngestRun.status == "success")
        .order_by(IngestRun.finished_at.desc())
        .limit(1)
    )
    return {
        "status": "ok",
        "last_successful_ingest_at": last_successful.isoformat() if last_successful else None,
    }
```

- [ ] **Step 4: eseguire il test e verificare che passi**

Run: `cd backend && pytest tests/test_health.py -v`
Expected: PASS.

- [ ] **Step 5: commit**

```bash
git add backend/app/api/routes/health.py backend/tests/test_health.py
git commit -m "feat: expose last successful ingest timestamp on /healthz"
```

---

### Task 7: Frontend — footer con orario ultimo aggiornamento

**Files:**
- Modify: `frontend/lib/types.ts`
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/lib/i18n/dictionaries.ts`
- Modify: `frontend/app/layout.tsx`

**Interfaces:**
- Consumes: `GET /healthz` (Task 6).
- Produces: nessuna nuova interfaccia consumata da altri task.

- [ ] **Step 1: tipo `HealthzResponse`**

In `frontend/lib/types.ts`, in fondo al file:

```ts
export interface HealthzResponse {
  status: string;
  last_successful_ingest_at: string | null;
}
```

- [ ] **Step 2: funzione client**

In `frontend/lib/api.ts`, aggiungere `HealthzResponse` all'import in cima:

```ts
import type {
  AwayFixturesResponse,
  BriefResponse,
  CompetitionOut,
  HealthzResponse,
  LiveMatchOut,
  MatchListResponse,
  MatchOut,
  MomentumOverview,
  MomentumPoint,
  PredictionCommunityStats,
  PredictionOut,
  PredictionOutcome,
  PredictionStats,
} from "./types";
```

e in fondo al file, prima di `export { ApiError };`:

```ts
export function getHealthz(): Promise<HealthzResponse> {
  return apiFetch<HealthzResponse>("/healthz");
}
```

(`/healthz` è montato alla radice, non sotto `/api/v1` — vedi `backend/app/main.py`; `apiFetch` prepende solo `API_BASE_URL`, quindi il path resta `/healthz`.)

- [ ] **Step 3: chiavi i18n**

In `frontend/lib/i18n/dictionaries.ts`, nell'interfaccia `Dictionary`, dopo `footer: string;` (riga 21):

```ts
  footer: string;
  footerUpdatedAt: (time: string) => string;
```

Nel dizionario italiano, subito dopo la voce `footer:` esistente (riga ~191-192):

```ts
    footer:
      "Dati indicativi da football-data.org (fallback Wikipedia). Progetto personale, non affiliato alla Juventus FC.",
    footerUpdatedAt: (time) => `Dati aggiornati alle ${time}`,
```

Nel dizionario inglese, subito dopo la voce `footer:` esistente (riga ~362-363):

```ts
    footer:
      "Indicative data from football-data.org (Wikipedia fallback). Personal project, not affiliated with Juventus FC.",
    footerUpdatedAt: (time) => `Data last updated at ${time}`,
```

- [ ] **Step 4: usarla nel layout**

In `frontend/app/layout.tsx`:

1. Aggiungere l'import:

```ts
import { getHealthz, getUpcomingMatches } from "@/lib/api";
```

(sostituisce l'import esistente `import { getUpcomingMatches } from "@/lib/api";`)

2. Nel corpo di `RootLayout`, dopo `const nextMatch = await getUpcomingMatches(1).catch(() => []);`:

```tsx
  const healthz = await getHealthz().catch(() => null);
  const lastUpdated = healthz?.last_successful_ingest_at
    ? new Date(healthz.last_successful_ingest_at).toLocaleTimeString(locale === "en" ? "en-GB" : "it-IT", {
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;
```

3. Sostituire il footer:

```tsx
          <footer className="site-footer">
            <div>{dict.footer}</div>
            {lastUpdated && <div style={{ marginTop: 4 }}>{dict.footerUpdatedAt(lastUpdated)}</div>}
          </footer>
```

- [ ] **Step 5: verifica tipo/build**

Run: `cd frontend && npm run build`
Expected: build passa senza errori TypeScript.

- [ ] **Step 6: verifica visiva**

Con backend e frontend avviati e almeno una riga `success` in `ingest_runs` (creala a mano via `psql` se non hai ancora fatto un run reale, oppure aspetta il Task 9), ricaricare qualunque pagina e verificare che il footer mostri "Dati aggiornati alle HH:MM" sotto la riga esistente. Senza righe in `ingest_runs`, il footer mostra solo la riga esistente (nessuna riga vuota/rotta).

- [ ] **Step 7: commit**

```bash
git add frontend/lib/types.ts frontend/lib/api.ts frontend/lib/i18n/dictionaries.ts frontend/app/layout.tsx
git commit -m "feat: show last-updated time in the footer"
```

---

### Task 8: Refresh giornaliero in cloud via GitHub Actions

**Files:**
- Create: `.github/workflows/scheduled-ingest.yml`
- Modify: `README.md` (sezione "Deploy in produzione")

**Interfaces:** nessuna (workflow CI, non consumato da altro codice).

- [ ] **Step 1: creare il workflow**

`.github/workflows/scheduled-ingest.yml`:

```yaml
name: Scheduled Ingest

on:
  schedule:
    - cron: "0 2 * * *"
  workflow_dispatch:

jobs:
  ingest:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    env:
      DATABASE_URL: ${{ secrets.NEON_DATABASE_URL }}
      FOOTBALL_DATA_API_KEY: ${{ secrets.FOOTBALL_DATA_API_KEY }}
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.11"
          cache: "pip"
          cache-dependency-path: backend/requirements.txt
      - run: pip install -r requirements.txt
      - run: alembic upgrade head
      - run: python -m app.ingestion.ingest
```

Note di design:
- `workflow_dispatch` permette un run manuale da GitHub UI/CLI per verificare che sia verde senza aspettare le 2:00 (vedi Task 9 per il run di verifica).
- `alembic upgrade head` prima dell'ingest protegge da schema drift se una migrazione (es. Task 4) non è ancora stata applicata al DB di produzione.
- Nessun `--seasons`: `python -m app.ingestion.ingest` senza argomenti usa `default_seasons()`, che si auto-aggiorna ogni stagione (vedi `backend/app/ingestion/ingest.py`).
- `DATABASE_URL` deve essere la connection string **diretta** di Neon (non quella pooled usata da Render), come da guideline del piano prodotto — le connessioni pooled non sono pensate per DDL/migrazioni.

- [ ] **Step 2: documentare i secret richiesti nel README**

In `README.md`, sezione "Deploy in produzione", subito dopo il punto 3 esistente ("**Vercel**: importa `frontend/`..."), aggiungere un nuovo punto 4:

```markdown
4. **Refresh giornaliero (GitHub Actions)**: il workflow
   `.github/workflows/scheduled-ingest.yml` gira ogni notte alle 2:00 UTC sul
   codice di `main`, senza bisogno del Mac acceso o di Docker. Richiede due
   secret del repository (Settings → Secrets and variables → Actions):
   `NEON_DATABASE_URL` (connection string **diretta**, non pooled, di Neon) e
   `FOOTBALL_DATA_API_KEY`. Verificalo con un run manuale
   (`gh workflow run scheduled-ingest.yml` o dal tab Actions) prima di
   fidartene: deve risultare verde.
```

- [ ] **Step 3: validare la sintassi YAML**

Run: `cd /Users/simonemezzabotta/Coding_Projects/juventum && python3 -c "import yaml, sys; yaml.safe_load(open('.github/workflows/scheduled-ingest.yml'))" 2>/dev/null || python3 -c "import json; print('yaml module not available, skipping — verify by eye')"`
Expected: nessun errore di parsing (se il modulo `yaml` non è installato, rileggere il file a mano confrontandolo con `.github/workflows/ci.yml` per coerenza di indentazione).

- [ ] **Step 4: commit**

```bash
git add .github/workflows/scheduled-ingest.yml README.md
git commit -m "feat: run the daily ingest on a GitHub Actions cron instead of the local Mac"
```

Il run di verifica effettivo (workflow verde) richiede i secret configurati e un `DATABASE_URL` di produzione raggiungibile — vedi Task 9.

---

### Task 9: Runbook operativo — ingestione reale, deploy, chiusura backtest

Questi passi non sono TDD: richiedono credenziali/account che solo l'utente possiede (chiave football-data.org già in `backend/.env` per lo sviluppo locale, account Neon/Render/Vercel, repository secrets di GitHub) e producono dati reali, non codice. Vanno eseguiti nell'ordine indicato dopo che i Task 1-8 sono stati committati.

- [ ] **Step 1: prima ingestione reale in locale**

```bash
cd backend
python -m app.ingestion.ingest   # usa FOOTBALL_DATA_API_KEY da backend/.env
```

Verifica attesa: ~4 stagioni (2023-24 → 2026-27) arrivano da football-data.org, le più vecchie restano su Wikipedia con `is_approximate_date=true` (Task 2/3). Se una stagione fallisce con 403 (fuori dalla finestra free tier), il fallback Wikipedia scatta da solo (comportamento già su `main`, vedi `_ingest_competition_from_football_data`).

- [ ] **Step 2: controllare i nomi squadra**

```bash
python scripts/check_team_names.py
```

Per ogni nome in "UNRECOGNIZED", aggiungere l'alias in `backend/app/core/teams.py` (`ALIASES`), rilanciare `python -m app.ingestion.ingest`, ripetere finché la lista è vuota. Senza questo passo, la storia Elo di quel club si spezza in due spelling diversi.

- [ ] **Step 3: verificare la riga in `ingest_runs`**

```bash
psql "$DATABASE_URL" -c "select started_at, finished_at, status, matches_upserted, source_summary from ingest_runs order by id desc limit 1;"
```

Deve esserci una riga `status='success'` con `matches_upserted` coerente col numero di partite ingerite.

- [ ] **Step 4: deploy — Neon**

Creare un progetto Postgres su Neon. Copiare la connection string **pooled** per `DATABASE_URL` di Render (Step 5) e quella **diretta** per `NEON_DATABASE_URL` del secret GitHub Actions (Task 8) e per lanciare `alembic upgrade head` a mano se serve.

- [ ] **Step 5: deploy — Render**

Nuovo Web Service da Docker, root directory `backend/`, health check `/healthz`. Configurare le env: `DATABASE_URL` (Neon pooled), `FOOTBALL_DATA_API_KEY`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `ENABLE_LLM_BRIEF`, `CORS_ORIGINS` (dominio Vercel, aggiunto dopo lo Step 6), `ADMIN_TOKEN` (generare un valore casuale, es. `openssl rand -hex 32`), `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT`. Dopo il primo deploy, lanciare l'ingestione una volta via Render Shell (`python -m app.ingestion.ingest`) per popolare il DB di produzione, e ripetere lo Step 2 (`check_team_names.py`) contro il DB Neon.

- [ ] **Step 6: deploy — Vercel**

Importare `frontend/` come root directory. Env: `NEXT_PUBLIC_API_BASE_URL` (URL pubblico del backend Render), `NEXT_PUBLIC_VAPID_PUBLIC_KEY` (deve coincidere col `VAPID_PUBLIC_KEY` di Render). Richiede un redeploy se cambiate (compilate a build time). Aggiornare `CORS_ORIGINS` su Render col dominio Vercel effettivo e ridispiegare il backend.

- [ ] **Step 7: aggiornare i placeholder del README**

Sostituire `<link Vercel qui dopo il deploy>` e `<link Render qui dopo il deploy>` in `README.md` con gli URL reali. Creare `docs/screenshots/overview.png` (screenshot reale dell'Overview con dati veri) così il riferimento nel README smette di puntare a un file inesistente.

- [ ] **Step 8: configurare i secret di GitHub Actions**

```bash
gh secret set NEON_DATABASE_URL --body "<connection string diretta Neon>"
gh secret set FOOTBALL_DATA_API_KEY --body "<chiave football-data.org>"
gh workflow run scheduled-ingest.yml
```

Verificare che il run risulti verde (`gh run list --workflow=scheduled-ingest.yml`) prima di considerare chiuso questo task.

- [ ] **Step 9: dismettere il cron locale di ingest**

Una volta che il workflow GitHub Actions ha almeno un run verde, il job `launchd` locale diventa ridondante (stessa logica, ma dipende dal Mac acceso):

```bash
launchctl unload ~/Library/LaunchAgents/com.juventum.scheduled-ingest.plist
```

Lasciare il file del plist nel repo per riattivarlo se mai servisse di nuovo il refresh locale, ma non ricaricarlo di default.

- [ ] **Step 10: live poll — cron-job.org**

Generare `ADMIN_TOKEN` (già fatto allo Step 5 se non prima) e registrare un cron job gratuito su cron-job.org che ogni 2-3 minuti fa:

```
POST https://<backend-render>.onrender.com/api/v1/admin/poll-live
Header: X-Admin-Token: <lo stesso ADMIN_TOKEN di Render>
```

Questo sostituisce (in produzione) `scripts/scheduled_live_poll.sh`, che resta utile solo per testare il live in locale puntando `BACKEND_URL` al backend locale. Lo stesso servizio cron-job.org può anche pingare `GET /healthz` ogni 10 minuti per tenere sveglio il backend Render (prerequisito del punto 4/10 della roadmap, non ulteriormente dettagliato in questo piano).

- [ ] **Step 11: chiudere il backtest con date reali**

Dopo che Neon ha dati reali per tutte le 6+ stagioni (Step 4-5):

```bash
cd backend
python -m app.ingestion.ingest --seasons 2019-2020,2020-2021,2021-2022,2022-2023,2023-2024,2024-2025
python scripts/backtest_win_probability.py
```

Prendere l'output (log loss/Brier/accuracy per fold, media CV, tabella di calibrazione) e aggiungere una nuova sezione in `docs/backtest.md`, sotto il titolo esistente `## Elo completo con date reali (football-data.org) — definitivo` (che oggi contiene solo "TBD — ..."), con lo stesso formato delle due sezioni precedenti del documento (holdout singolo, CV leave-one-season-out, calibrazione, confronto con la baseline "Elo Wikipedia intera lega").

Criterio di decisione (dal documento stesso): se il log loss medio in CV migliora rispetto alla riga "Attuale" della sezione "Elo completo via Wikipedia" (0.9530), aggiornare `DRAW_PEAK_PROBABILITY`/`DRAW_DECAY_SCALE` in `backend/app/features/win_probability.py` alle nuove costanti trovate dalla grid search dello script, in un commit dedicato separato dall'aggiornamento del documento. Se non migliora, lasciare le costanti attuali (0.28/400) e scriverlo esplicitamente nel documento.

```bash
git add docs/backtest.md
git commit -m "docs: close the win-probability backtest with real match dates"
# solo se le costanti cambiano:
git add backend/app/features/win_probability.py
git commit -m "feat: retune win-probability constants on the real-date backtest"
```

---

## Copertura gap (tracciabilità con l'analisi prodotto)

| Gap | Coperto da |
|---|---|
| G1 (dati stantii/segnaposto) | Task 9 Step 1-2, 4-6 |
| G2 (chiave football-data mai usata) | Task 9 Step 1 |
| G3 (refresh rotto per immagine Docker vecchia) | Task 1 |
| G4 (due database che divergono) | Task 1 Step 2 |
| G5 (live poll locale non attivo) | Task 9 Step 10 |
| G6 (nessun deploy) | Task 9 Step 4-7 |
| G7 (backtest mai completato) | Task 9 Step 11 |
| Insidia "date Wikipedia placeholder" | Task 2, Task 3 |
| "Fatto quando": prossime 5 partite con orario/stadio | Task 9 Step 1 (dati reali attivano `UpcomingMatches`, già funzionante) |
| "Fatto quando": footer con orario aggiornamento | Task 4, 5, 6, 7 |
| "Fatto quando": link README funzionante | Task 9 Step 7 |
| "Fatto quando": workflow cron con run verde | Task 8, Task 9 Step 8 |

**Fuori scope per questo piano** (esplicitamente rimandato dal documento prodotto): stadi europei aggiuntivi in `app/core/stadiums.py` (guideline 3 — "solo se si vuole la trasferta europea", non richiesto per il "fatto quando" di questo sviluppo).
