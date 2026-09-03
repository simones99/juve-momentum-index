# Prompt per Claude Code /superpowers – Progetto "Juve Momentum Index" (con Match Brief)

## Contesto e obiettivo

Voglio che tu, come Claude Code in modalità `/superpowers`, sviluppi un **MVP** chiamato **"Juve Momentum Index"**.

Obiettivi principali:

1. Costruire un **indice di forma della Juventus** (Momentum Index) nel tempo, basato su risultati ed eventualmente rating tipo Elo.
2. Esporre questo indice e le metriche principali in una **dashboard Streamlit**.
3. Aggiungere una feature **"Juve Match Brief"** che genera una breve anteprima/recap partita (numerica + testuale) usando le statistiche disponibili.

Il risultato deve poter girare **sia in locale sul mio Mac sia in container Docker**, in un singolo repo Python chiaro e testabile.

---

## Vincoli e aspettative generali

- Linguaggio: **Python 3.11+**.
- Gestione dipendenze: `uv` o `pip + requirements.txt` (scegli tu, ma mantieni l’uso semplice e compatibile con Docker).
- Storage dati: **DuckDB** o **SQLite** per tabelle match, statistiche, rating, salvato su un volume persistente.
- App: **Streamlit** con più pagine (Momentum Index, Match List, Match Brief).
- Ambiente target: Mac (anche Apple Silicon/ARM64), sia esecuzione diretta da terminale sia via Docker.
- Nessun bisogno di credenziali proprietarie: usa solo fonti dati pubbliche/scraping o repository di riferimento.
- Codice modulare, con docstring e qualche test sui calcoli principali.

Organizza il progetto con una struttura simile a questa:

```text
juve-momentum-index/
  pyproject.toml / requirements.txt
  Dockerfile
  docker-compose.yml
  .dockerignore
  src/
    data/
      ingest_matches.py
      sources/
        wikipedia_scraper.py
        api_fixtures.py
      models/
        schemas.py
    features/
      elo.py
      momentum_index.py
      match_stats.py
    app/
      app.py
      pages/
        01_overview.py
        02_momentum.py
        03_matches.py
        04_match_brief.py
  data/           # volume dati persistente (DB file, cache scraping)
  tests/
  README.md
```

Puoi adattarla, ma mantieni separati: ingestion dati, calcolo feature/indici, app Streamlit.

---

## Requisiti Docker (obbligatori)

### 1. Dockerfile

Crea un `Dockerfile` (single-stage o multi-stage, a tua scelta se semplifica) che:

- Usa un'immagine base ufficiale Python slim, compatibile sia con arm64 (Apple Silicon) sia con amd64 (es. `python:3.11-slim`).
- Installa le eventuali dipendenze di sistema richieste per lo scraping (es. librerie per `lxml`/parsing HTML) e, se serve, per Playwright/Chromium **solo se effettivamente usi scraping headless**; altrimenti mantieni l'immagine leggera.
- Copia solo i file necessari (usa un `.dockerignore` per escludere `.venv`, `__pycache__`, `.git`, cache dati grandi, ecc.).
- Installa le dipendenze Python (`uv sync` o `pip install -r requirements.txt`).
- Espone la porta **8501** (default Streamlit).
- Definisce un `HEALTHCHECK` semplice che verifica che Streamlit risponda.
- Usa come `CMD`/`ENTRYPOINT` l'avvio dell'app:
  ```bash
  streamlit run src/app/app.py --server.address=0.0.0.0 --server.port=8501
  ```
- Esegue l'app con un **utente non-root** per buona pratica di sicurezza.

### 2. docker-compose.yml

Crea un `docker-compose.yml` che definisca almeno un servizio `app`:

```yaml
services:
  app:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
    environment:
      - DB_PATH=/app/data/juve_momentum.duckdb
    restart: unless-stopped
```

Requisiti aggiuntivi:

- Il **volume** `./data:/app/data` deve garantire che il database (match, elo, momentum) e le eventuali cache di scraping sopravvivano al rebuild del container.
- Aggiungi un secondo servizio opzionale `ingest` per lanciare manualmente l'aggiornamento dati senza dover entrare nel container dell'app:
  ```yaml
  ingest:
    build: .
    volumes:
      - ./data:/app/data
    environment:
      - DB_PATH=/app/data/juve_momentum.duckdb
    command: ["python", "-m", "src.data.ingest_matches"]
    profiles: ["tools"]
  ```
  così può essere lanciato con `docker compose run --rm ingest`.

### 3. Configurazione tramite variabili d'ambiente

- Il path del database deve essere configurabile via variabile d'ambiente `DB_PATH`, con default sensato se non in Docker (es. `./data/juve_momentum.duckdb`).
- Se usi parametri per le stagioni da scaricare, rendili configurabili via variabile d'ambiente o argomento CLI (es. `SEASONS=2022-2023,2023-2024,2024-2025`).
- Nessun'altra configurazione sensibile è richiesta (dati pubblici, nessuna API key indispensabile per l'MVP).

### 4. Istruzioni d'uso (nel README)

Il README deve includere sia il flusso **locale (senza Docker)** sia quello **via Docker**, ad esempio:

**Senza Docker:**
```bash
uv sync
python -m src.data.ingest_matches
streamlit run src/app/app.py
```

**Con Docker:**
```bash
docker compose build
docker compose run --rm ingest        # scarica/aggiorna i dati la prima volta
docker compose up app                 # avvia la dashboard su http://localhost:8501
```

Spiega anche come rifare il refresh dei dati periodicamente (`docker compose run --rm ingest`) e dove trovare il file DB generato (`./data/juve_momentum.duckdb` sull'host, grazie al volume).

---

## Fonti e progetti GitHub di riferimento

Usa questi progetti come **ispirazione/guida** per scraping, modello Elo e strutturazione dati (non serve copiarli 1:1, ma puoi leggere il codice e riadattarlo):

- `elo_football_project`: estrae dati da Wikipedia sulle stagioni Serie A e calcola Elo per le squadre.
- `WebScrap-SerieA`: scraper Scrapy per dati partite Serie A, con output JSON per analisi.
- `serie-a-db` e `Serie-A-stats-analyzer`: costruzione di database risultati Serie A e script di analisi/classifica.
- `WhoScored_auto_scraper`: pipeline containerizzata (già usa Docker!) per dati evento WhoScored — buon riferimento pratico anche per il tuo setup Docker.

Per l’MVP, è sufficiente arrivare a **dati di risultato base** (data, avversario, casa/trasferta, gol fatti/subiti) per la Juventus in Serie A.

---

## Layer dati: cosa voglio avere in tabella

Definisci almeno queste tabelle (in DuckDB/SQLite):

1. `matches`
   - Colonne minime:
     - `match_id` (chiave primaria artificiale)
     - `season` (es. 2024-2025)
     - `date` (data partita)
     - `home_team`
     - `away_team`
     - `home_goals`
     - `away_goals`
     - `competition` (es. Serie A; possiamo iniziare solo con Serie A)
   - Per ora concentrati su partite dove **home_team == "Juventus"** o **away_team == "Juventus"**.

2. `elo_ratings` (o vista calcolata)
   - `date`
   - `team`
   - `elo`

3. `juve_momentum`
   - `date`
   - `season`
   - `opponent`
   - `home_away` (H/A)
   - `result` (W/D/L)
   - `goals_for`
   - `goals_against`
   - `elo_before`
   - `elo_after`
   - eventuali **rolling stats** (vedi sotto).

Se per l’MVP è più semplice, puoi calcolare Elo on‑the‑fly in Python e non persistere `elo_ratings`, ma è preferibile avere almeno una tabella/vista dedicata.

---

## Ingestion dati

### Priorità: usare dati pubblici facilmente accessibili

Implementa almeno uno di questi approcci (scegli il più veloce/stabile, e ricorda che deve funzionare anche dentro Docker):

1. **Scraping Wikipedia** (ispirandoti a `elo_football_project`)
   - Per 1–3 stagioni recenti (es. 2022-2023, 2023-2024, 2024-2025), estrai le tabelle con i risultati di Serie A dalle pagine Wikipedia delle stagioni.
   - Pulisci i dati in un DataFrame con le colonne richieste in `matches`.

2. **Uso di un progetto Serie A DB** (come `serie-a-db`) come sorgente già strutturata
   - Se è più facile, clona `serie-a-db`, esegui lo script che popola il DB e poi estrai solo le partite di Juventus.

Nel file `src/data/ingest_matches.py` voglio una funzione principale tipo:

```python
def update_matches(seasons: list[str] | None = None) -> None:
    """Scarica/aggiorna i dati partite per le stagioni richieste e li salva nel DB locale."""
```

Lo script deve poter essere lanciato con:

```bash
python -m src.data.ingest_matches
```

sia in locale sia via `docker compose run --rm ingest`.

---

## Calcolo Elo e rolling stats (Momentum Index core)

### 1. Base Elo

Implementa un modulo `src/features/elo.py` che:

- definisce parametri base (K‑factor, rating iniziale per tutte le squadre, ecc.);
- prende in input il DataFrame dei `matches` e restituisce un DataFrame arricchito con `elo_before` e `elo_after` per ogni squadra;
- per `juve_momentum` estrai solo le righe dove gioca la Juventus e assegna a ciascuna partita l’Elo della Juve prima e dopo.

### 2. Rolling stats

Nel modulo `src/features/momentum_index.py`, calcola per la Juventus, ordinando le partite per data:

- **Punti per partita** (3/1/0) e rolling media su finestre di 5 e 10 partite.
- **Differenza reti media** (goals_for - goals_against) rolling su 5 e 10 partite.
- **Elo normalizzato**: porta `elo` su scala 0–100 rispetto al minimo/massimo della Juve nelle stagioni considerate.

Definisci infine un **Momentum Index** aggregato, ad esempio:

\( Momentum = 0.5 * Elo_{norm} + 0.25 * Punti_{rolling5} + 0.25 * DiffReti_{rolling5} \)

Puoi scegliere una formula semplice, ma scrivila come funzione separata e documentala.

Il risultato deve essere `juve_momentum` con una colonna `momentum_index` per ogni partita.

---

## Feature B: "Juve Match Brief"

Questa feature si appoggia agli stessi dati/indici.

### 1. Caso d’uso A – Brief pre‑partita

Per una **partita futura** (fixture) o “prossimo avversario”:

- Recupera le ultime N partite della Juve (es. 5 o 10).
- Calcola e mostra:
  - forma recente (media momentum_index, punti, diff reti);
  - andamento Elo (trend crescente/decrescente);
  - record recente vs l’avversario se disponibile (anche solo W/D/L nelle ultime X gare).

### 2. Caso d’uso B – Brief post‑partita

Per una **partita già giocata**:

- Mostra risultato, gol, diff Elo.
- Confronta la partita con le ultime N: è stato sopra o sotto la media recente in termini di diff reti/risultato?

### Output atteso (per ora senza LLM, solo Dati + Testo Template)

Implementa funzioni che restituiscono un dizionario con:

- campi numerici (punti, momentum medio, diff reti);
- brevi stringhe generate tramite template Python (es. `f"La Juve arriva da {wins} vittorie nelle ultime {n} partite"`).

In futuro l’utente potrà sostituire i template con chiamate LLM, ma l’MVP deve funzionare anche senza API di AI esterne, sia in locale sia in Docker.

---

## Streamlit app – requisiti funzionali

Costruisci una app Streamlit con almeno queste pagine:

### Pagina 1 – Overview

- Grafico a linea del `momentum_index` nel tempo per 2–3 stagioni.
- Possibilità di filtrare per stagione.
- Alcuni KPI:
  - massimo/minimo Momentum nella stagione selezionata;
  - serie di partite positive (streak più lunga di W consecutive, ecc.).

### Pagina 2 – Momentum Details

- Tabella partite Juve con colonne base + `momentum_index`, `elo_before`, `elo_after`.
- Filtri per stagione, tipo partita (casa/trasferta), range di date.
- Grafico che mostra Elo vs Momentum nello stesso grafico o in due subplot.

### Pagina 3 – Matches

- Lista/Tabella di tutte le partite con filtri (stagione, avversario, casa/trasferta, risultato).
- Possibilità di cliccare/selezionare una partita per aprire la pagina "Match Brief" (anche con `st.session_state` o query param semplice).

### Pagina 4 – Match Brief

- Selezione manuale della partita (dropdown stagione + avversario + data, o partite future/past).
- Per partite passate:
  - sezione “Dati”: risultato, Elo prima/dopo, Momentum prima/dopo, diff reti.
  - sezione “Testo”: 3–5 frasi generate da template che riassumono la performance.
- Per partite future (se hai implementato fixture):
  - usa le ultime N partite per creare il pre‑match brief come sopra.

UX minimale, ma chiara: titoli, brevi spiegazioni, colori sobri.

---

## Automazione, test, documentazione

1. **Script aggiornamento dati**
   - Script CLI (es. `python -m src.data.ingest_matches`) che aggiorna/ricostruisce il DB per le stagioni indicate.
   - Deve funzionare sia in locale sia via `docker compose run --rm ingest`.

2. **Test**
   - Aggiungi test unitari per:
     - calcolo Elo su un piccolo set fittizio di match,
     - calcolo rolling stats,
     - composizione del `momentum_index`.
   - I test devono poter girare sia con `pytest` in locale sia (idealmente) dentro il container.

3. **README.md**
   - Spiega:
     - come installare dipendenze in locale;
     - come aggiornare i dati (locale e Docker);
     - come lanciare Streamlit (locale e Docker);
     - dove risiedono i dati persistenti (volume `./data`);
     - che i dati sono indicativi e provengono da scraping/open data (Wikipedia/altro).

---

## Cosa mi aspetto da te in modalità /superpowers

Quando incollerò questo prompt dopo `/superpowers`, voglio che tu:

1. Crei la struttura di progetto (cartelle, file base, gestione dipendenze, Dockerfile, docker-compose.yml, .dockerignore).
2. Implementi la pipeline di ingestion (almeno per 1–3 stagioni recenti di Serie A) usando Wikipedia o un progetto Serie A esistente come sorgente.
3. Implementi il calcolo Elo, le rolling stats e il `momentum_index` per la Juventus.
4. Implementi l’app Streamlit con le 4 pagine descritte.
5. Aggiunga alcuni test base e un README chiaro che copra sia l'uso locale sia quello via Docker.
6. Verifichi (concettualmente o con build/test se l'ambiente lo consente) che il Dockerfile costruisca correttamente e che `docker compose up app` esponga la dashboard sulla porta 8501.

Puoi usare shell per clonare repo di riferimento, studiare il codice e portare logiche utili nel nuovo progetto, ma il risultato finale deve essere **unico e auto‑contenuto**, pronto all’uso sia in locale sia containerizzato.
