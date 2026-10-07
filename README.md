# Juve Momentum Index

![CI](https://github.com/simones99/juve-momentum-index/actions/workflows/ci.yml/badge.svg)

_Versione italiana: [README.it.md](README.it.md)._

Juve Momentum Index is a small end-to-end data project about Juventus FC. A
scheduled job ingests every Serie A and Champions League match for a window
of seasons. From those matches it computes an Elo rating for each team and a
0–100 Momentum Index for Juventus, which combines the Elo rating with recent
form. A Next.js dashboard shows both over time. The same Elo ratings feed a
simple win/draw/loss probability model, which is backtested with
leave-one-season-out cross-validation against two naive baselines. Both the
results and the model's weaknesses are documented below. This is a personal
project and is not affiliated with Juventus FC.

**Live demo:** not deployed yet.

![Overview page](docs/screenshots/overview.png)

![Momentum Details page: Elo rating and Momentum Index per match](docs/screenshots/momentum.png)

_Screenshots taken from a local `docker compose` run on 2026-10-07. That run
ingested the default window (current season plus the three before it), so the
charts start in 2023._

## Architecture

```
Next.js dashboard  ──HTTP──▶  FastAPI backend  ──SQLAlchemy──▶  PostgreSQL (Alembic migrations)
                                    │
                                    ├─ ingestion job: football-data.org (primary), Wikipedia (Serie A fallback)
                                    ├─ derived tables: Elo ratings + Momentum Index, rebuilt after every ingest
                                    ├─ Match Brief: template text, optionally rewritten by an LLM via OpenRouter
                                    └─ Away Trips: Nominatim (geocoding) + OSRM (road routing)
```

- **Backend** (`backend/`): Python, FastAPI, SQLAlchemy 2, Alembic, pandas.
  The API is under `/api/v1/*`, and `/healthz` reports when the last
  successful ingest ran.
- **Database**: PostgreSQL 16. The schema is managed by Alembic
  (`backend/alembic/versions/`). Raw matches live in `matches`. The derived
  tables `elo_ratings` and `juve_momentum` are dropped and rebuilt from
  `matches` on every ingest (`backend/app/features/recompute.py`).
- **Ingestion** (`backend/app/ingestion/ingest.py`): one CLI job,
  `python -m app.ingestion.ingest [--seasons 2023-2024,...]`. It runs
  manually, as the `ingest` service in Docker Compose, on demand through
  `.github/workflows/scheduled-ingest.yml` (needs the `NEON_DATABASE_URL`
  and `FOOTBALL_DATA_API_KEY` secrets), or nightly through a macOS `launchd`
  job (`scripts/`; the plist files use a `__REPO_DIR__` placeholder,
  replaced on install with
  `sed "s#__REPO_DIR__#$PWD#g" scripts/<file>.plist > ~/Library/LaunchAgents/<file>.plist`). Each ingest run is logged in the `ingest_runs` table.
- **Frontend** (`frontend/`): Next.js 16 (App Router), TypeScript, Recharts,
  with Italian/English UI strings. Pages: Overview, Momentum Details,
  Matches, Match Brief, Away Trips, Predictions.
- **Extras, not part of the analysis**: browser push notifications, a live
  score poller, and a "beat the model" prediction game in which users'
  1/X/2 picks are scored against the model's argmax.

## Data sources and terms of use

| Source | Used for | Notes on terms |
|---|---|---|
| [football-data.org](https://www.football-data.org/) API v4 | Primary source: every Serie A (`SA`) and Champions League (`CL`) match, with dates, venues and status | Needs a personal API key. The free tier is limited to 10 requests/minute and a rolling window of about four seasons; older seasons return HTTP 403. Its terms ([about page](https://www.football-data.org/about)) require the attribution "Football data provided by the Football-Data.org API", shown in the app footer, and leave the rights to club logos to the user. Crest images are therefore hidden by default; set `NEXT_PUBLIC_SHOW_CRESTS=true` only if you hold those rights. They are linked from football-data.org's CDN, never stored here. |
| Wikipedia, "20XX–YY Serie A" season pages ([example](https://en.wikipedia.org/wiki/2021%E2%80%9322_Serie_A)) | Fallback for Serie A results only, used when the API call for a season fails | Wikipedia text is licensed [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Only match results (facts) are extracted. The pages give no per-match date, so these rows get a season-start placeholder date that the UI flags as approximate. |
| [Nominatim](https://nominatim.org/) (OpenStreetMap) | Geocoding the user's starting city on the Away Trips page | Subject to the [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/): low request volume and an identifying User-Agent. Data © OpenStreetMap contributors, [ODbL](https://www.openstreetmap.org/copyright). |
| [OSRM](https://project-osrm.org/) public demo server | Driving distance and time for Away Trips | The demo server has no SLA and is not meant for production traffic. If it cannot be reached, the app falls back to a straight-line estimate and marks it `is_estimated`. |

The repository contains no raw data dumps. Every dataset is downloaded at run
time with the user's own API key.

## Methodology

### Elo rating — `backend/app/features/elo.py`

Ratings are computed over **all** ingested matches in chronological order, not
only Juventus fixtures, so every opponent's rating comes from its own league
results. Unplayed fixtures are skipped.

- Initial rating: `INITIAL_ELO = 1500`, assigned to each team at its first
  appearance in the ingested window.
- Expected score of the home side, with home advantage `H = 65` Elo points:

  `E_home = 1 / (1 + 10^((R_away − (R_home + H)) / 400))`
- Update with constant `K = 20`, where `S_home` is 1 for a win, 0.5 for a
  draw and 0 for a loss. The update is zero-sum:

  `R_home' = R_home + K · (S_home − E_home)`, `R_away' = R_away − K · (S_home − E_home)`

K and H are fixed by hand. They were not fitted.

### Momentum Index — `backend/app/features/momentum_index.py`, `rolling_stats.py`

The index is computed for each Juventus match, using all Juventus matches in
the database (Serie A and Champions League) sorted by date:

| Component | Definition | Weight |
|---|---|---|
| Elo | Juventus' post-match Elo (`elo_after`), min–max scaled to 0–100 over all stored Juventus matches | 0.50 |
| Points form | Mean points per match (W=3, D=1, L=0) over the **previous** 5 matches (`shift(1).rolling(5, min_periods=1)`), min–max scaled to 0–100 | 0.25 |
| Goal-difference form | Mean goal difference over the previous 5 matches, computed the same way and min–max scaled to 0–100 | 0.25 |

`Momentum = 0.5 · Elo_norm + 0.25 · Points_norm + 0.25 · GoalDiff_norm`, which
lies in [0, 100]. The first match has no form history, so its form components
are set to a neutral 50. A constant series is also mapped to 50 instead of
dividing by zero. Ten-match rolling values are also computed and stored, but they
are not part of the index.

The weights are a design choice, not an estimate. The index is a descriptive
summary and has not been validated as a predictor (see Limitations).

### Win/draw/loss probabilities — `backend/app/features/win_probability.py`

Elo's expected score is a points share, not a three-way distribution, so a
draw model is layered on top of it:

- `d = (R_home + H) − R_away`
- `P(draw) = 0.28 · exp(−0.5 · (d / 400)²)`, a Gaussian in the rating gap
  that peaks at 0.28 when the two sides are level
  (`DRAW_PEAK_PROBABILITY = 0.28`, `DRAW_DECAY_SCALE = 400`)
- `P(home) = E_home · (1 − P(draw))`, `P(away) = (1 − E_home) · (1 − P(draw))`

At prediction time, each team's most recent `elo_after` is used (1500 if the
team has never been seen). No separate recalibration step is applied, such as
Platt scaling or isotonic regression. "Calibration" here means two things:
1. the two draw constants were selected by grid search under
   leave-one-season-out cross-validation;
2. the result is checked against a reliability table (below).

The in-play adjustment that shifts probability mass towards the leading side
(`adjust_live_probabilities`) has **not** been backtested and is for display
only.

## Backtest results

The full log, including earlier iterations, is in
[`docs/backtest.md`](docs/backtest.md). It was produced by
`backend/scripts/backtest_win_probability.py`. Pre-match ratings
(`elo_before`) are used for both teams, so a match's own result never
reaches its prediction.

**Dataset:** 290 Juventus matches over 8 seasons: Serie A throughout, plus
Champions League where football-data.org provided it. The seasons run
from 2019-20 to 2026-27, and the backtest was run on 2026-09-15. Seasons 2023-24 onwards come from
football-data.org with real dates. Seasons 2019-20 to 2022-23 come from the
Wikipedia fallback with placeholder dates. The 2026-27 season was in
progress and contributed only 4 matches.

**Leave-one-season-out cross-validation (8 folds), mean ± std across folds:**

| Model | Log loss (± std) | Brier | Accuracy |
|---|---|---|---|
| Uniform baseline (1/3 each) | 1.0986 (±0.000) | 0.6667 | 0.542 |
| Frequency baseline (training-set W/D/L shares) | 1.0096 (±0.047) | 0.6040 | 0.542 |
| **Elo model, shipped constants (0.28 / 400)** | **0.9649 (±0.046)** | **0.5733** | 0.550 |
| Elo model, constants re-tuned on each training fold | 0.9717 (±0.038) | 0.5784 | 0.550 |

The Brier score is summed over the three outcomes, so it ranges from 0 to 2
and the uniform baseline scores 0.667. Accuracy is the accuracy of the argmax
prediction, and it barely separates the models. The frequency baseline always
predicts a Juventus win, which was the actual result in 54.2% of matches.

**Per-fold log loss:**

| Held-out season | n | Shipped constants | Re-tuned per fold |
|---|---|---|---|
| 2019-2020 | 38 | 0.908 | 0.937 |
| 2020-2021 | 38 | 0.925 | 0.928 |
| 2021-2022 | 38 | 0.992 | 0.993 |
| 2022-2023 | 38 | 0.903 | 0.924 |
| 2023-2024 | 38 | 0.998 | 0.998 |
| 2024-2025 | 48 | 1.034 | 1.034 |
| 2025-2026 | 48 | 1.003 | 1.003 |
| 2026-2027 | 4 | 0.956 | 0.957 |

**Reliability of P(Juventus win), shipped constants, full dataset** (five
equal-count buckets, sorted by predicted probability):

| Bucket | n | Mean predicted | Observed win rate |
|---|---|---|---|
| 1 | 58 | 0.31 | 0.29 |
| 2 | 58 | 0.44 | 0.47 |
| 3 | 58 | 0.49 | 0.60 |
| 4 | 58 | 0.56 | 0.67 |
| 5 | 58 | 0.65 | 0.67 |

**How the results changed as the data improved** (mean CV log loss of the
shipped constants; the datasets differ, so the rows are not strictly
comparable):

| Elo input | Folds / matches | Elo model | Frequency baseline |
|---|---|---|---|
| Juventus matches only (opponents reset to 1500) | 6 / 228 | 0.9892 | 0.9954 |
| Full league from Wikipedia, approximate within-season order | 6 / 228 | 0.9530 | 0.9954 |
| Full league, real dates for 2023-24 onwards | 8 / 290 | 0.9649 | 1.0096 |

### Limitations

The Elo model beats both baselines on average log loss and Brier score. The
margin over the frequency baseline is modest (0.965 vs 1.010), though, and
about the size of the fold-to-fold standard deviation. No paired significance
test or bootstrap interval has been run. The sample is small: 290 matches of
a single club, with test folds of 38–48 matches and one fold of only 4.

The shipped draw constants (0.28 / 400) were chosen with earlier
cross-validation runs on the 2019-20 to 2024-25 seasons, and those seasons
are also in this evaluation. The shipped-constants row is therefore slightly
optimistic. The honest out-of-sample figure is the per-fold re-tuned row
(0.972), which still beats the frequency baseline.

The reliability table shows that the model systematically **underestimates**
Juventus' win probability in the middle and upper buckets (by about 11
points in buckets 3 and 4). The likely causes are structural:
- the draw heuristic has only two parameters;
- the Elo update ignores goal margin;
- there is no between-season regression.

In addition:
- The four Wikipedia-sourced seasons have placeholder dates, so their
  within-season order is approximate.
- K and the home advantage were never tuned. The home advantage is also
  applied to Champions League matches played at neutral venues.
- Non-Italian Champions League clubs are rated on CL matches alone.

The Momentum Index has a different status: it is a hand-weighted descriptive
indicator, and it was never evaluated against outcomes.
- Its min–max scaling depends on the stored history, so adding seasons
  rescales past values.
- Its Elo component uses the post-match rating, while the form components
  use only the matches before. A match's own result therefore enters its
  index through Elo but not through form.

## Running locally

### With Docker Compose

Requirements: Docker. The root `.env` file is read by Compose. Variable names
only (see `backend/.env.example` for descriptions):

- `FOOTBALL_DATA_API_KEY`: required for real data (free key from football-data.org)
- `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `ENABLE_LLM_BRIEF`: optional LLM rewriting of Match Briefs (template text is used otherwise)
- `CORS_ORIGINS`, `ADMIN_TOKEN`: optional
- `SEASONS`: optional override for the ingest job, e.g. `2023-2024,2024-2025`

```bash
docker compose build
docker compose run --rm ingest       # migrates the DB and downloads/updates matches
docker compose up backend frontend   # dashboard http://localhost:3000, API http://localhost:8000/docs
docker compose stop                  # when done
```

The `db` service publishes port 5432. Stop any local PostgreSQL that is
already listening on that port first, or the two databases will silently
diverge.

To reproduce the backtest, ingest the eight seasons, then run the script
from a local backend virtualenv (see below) against the Compose database. The
script is not copied into the Docker image.

```bash
SEASONS=2019-2020,2020-2021,2021-2022,2022-2023,2023-2024,2024-2025,2025-2026,2026-2027 docker compose run --rm ingest
cd backend && DATABASE_URL=postgresql+psycopg://juventum:juventum@localhost:5432/juventum \
  python scripts/backtest_win_probability.py
```

football-data.org's free tier rejects the oldest seasons, so those fall back
to Wikipedia, as in the published run. Because the free tier's window keeps
moving, a rerun will not reproduce the published numbers exactly.

### Without Docker

Requirements: Python 3.11+, Node 20+, and a reachable PostgreSQL. Backend
variables go in `backend/.env` (template: `backend/.env.example`):
`DATABASE_URL` plus the variables listed above, and optionally
`LLM_TIMEOUT_SECONDS`, `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`,
`VAPID_SUBJECT`, `BACKEND_URL`. Frontend variables go in
`frontend/.env.local` (template: `frontend/.env.local.example`):
`NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_VAPID_PUBLIC_KEY`,
`NEXT_PUBLIC_SHOW_CRESTS` (default off, see the data sources table).

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
python -m app.ingestion.ingest
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

## Tests

```bash
cd backend
pytest -q
ruff check app tests scripts
```

The calculation tests (Elo, rolling stats, Momentum Index, probabilities)
are pure functions. API and ingestion tests need PostgreSQL. Locally,
`tests/conftest.py` creates a separate `<db>_test` database, so the
development data is never touched. For example, start only the database
with `docker compose up -d db` and keep the default
`DATABASE_URL=postgresql+psycopg://juventum:juventum@localhost:5432/juventum`.
In CI (`.github/workflows/ci.yml`), a PostgreSQL service container is used.
The same workflow also lints and builds the frontend.

## License

Code: MIT, see [LICENSE](LICENSE). Data belongs to its respective providers
(see [Data sources and terms of use](#data-sources-and-terms-of-use)). Club
names and crests are trademarks of their owners.
