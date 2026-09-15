# Sviluppo #2, Fase A — Fondamenta Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dare a Juventum un marchio proprio (nome + monogramma), una tipografia display coerente per numeri e titoli, i token CSS per sostenerla, e gli stemmi reali delle squadre dove oggi c'è solo testo — le fondamenta su cui le fasi B (Composizione) e C (Rifinitura) di Sviluppo #2 si appoggeranno.

**Architecture:** Nessuna migrazione DB. Gli stemmi sono un dizionario Python statico (`app/core/crests.py`), stesso pattern già in uso per `app/core/stadiums.py`, esposto via due campi opzionali sugli schemi Pydantic esistenti (`MatchOut`, `AwayFixtureOut`). La tipografia display (Oswald) è self-hosted via `next/font/google` e applicata tramite una CSS custom property, non globalmente sull'`<html>`. Il monogramma sostituisce l'SVG esistente nella sidebar con un wordmark testuale "JM" nella stessa font.

**Tech Stack:** FastAPI + Pydantic (backend), Next.js 16 App Router + TypeScript + CSS custom properties (frontend), `next/font/google`.

**Spec:** `docs/superpowers/specs/2026-09-15-sviluppo-2-fase-a-fondamenta-design.md` (design approvato), che a sua volta implementa `docs/analisi-prodotto-2026-09-09.md` sezione "2. Identità bianconera: design system premium" (gap G8-G13), sotto-scope Fase A.

## Global Constraints

- Tre colori: nero, bianco, oro (`--accent: #cdb079`). Nessun colore nuovo fuori da verde/arancio/rosso per gli esiti V/N/P.
- Nessun logo, wordmark o asset ufficiale Juventus. Bianco/nero/strisce sono linguaggio generico.
- Una sola famiglia di font aggiunta (Oswald), nessuna nuova libreria UI.
- Ogni dato mancante resta dichiarato/gestito graziosamente in UI, mai nascosto silenziosamente o causa di crash — uno stemma mancante non mostra nulla, non rompe il layout.
- Segue i pattern esistenti: modulo puro in `app/core/` per dati statici (come `stadiums.py`), schema Pydantic, nessuna migrazione se non serve.
- Verificare le API Next 16 in `frontend/node_modules/next/dist/docs/` prima di scrivere codice `next/font` — non assumere la sintassi da versioni precedenti di Next.js.
- Italiano prima, inglese mantenuto — ogni testo utente nuovo va in entrambe le lingue in `frontend/lib/i18n/dictionaries.ts` (per questo piano: nessun nuovo testo utente traducibile viene introdotto, salvo il sottotitolo del brand, gestito inline come già fa `generateMetadata` in `layout.tsx`, non con nuove chiavi dizionario).

---

## File Structure

**Backend — codice:**
- Create: `backend/app/core/crests.py` — dizionario statico `CRESTS: dict[str, str]`.
- Modify: `backend/app/schemas/match.py` — nuovi campi `home_crest_url`/`away_crest_url` su `MatchOut`.
- Modify: `backend/app/api/routes/matches.py` — valorizza i due campi in `match_to_out`.
- Modify: `backend/app/schemas/travel.py` — nuovo campo `crest_url` su `AwayFixtureOut`.
- Modify: `backend/app/api/routes/travel.py` — valorizza il campo in `_build_fixture_out`.

**Backend — test:**
- Create: `backend/tests/test_crests.py` — test puro su `CRESTS`.
- Modify: `backend/tests/test_api_matches.py` — verifica `home_crest_url`/`away_crest_url` in risposta.
- Modify: `backend/tests/test_api_travel.py` — verifica `crest_url` in risposta.

**Frontend:**
- Modify: `frontend/app/globals.css` — nuovi token (`--ink`, `--stripe`, scala tipografica), `--ink` applicato a `.kpi-card__value`.
- Modify: `frontend/app/layout.tsx` — setup font Oswald (`next/font/google`), nuovo monogramma "JM", brand name "Juventum" + sottotitolo.
- Modify: `frontend/lib/types.ts` — nuovi campi crest su `MatchOut`/`AwayFixtureOut`.
- Create: `frontend/components/TeamCrest.tsx` — componente condiviso per renderizzare uno stemma (o nulla).
- Modify: `frontend/components/MatchTable.tsx`, `frontend/components/UpcomingMatches.tsx`, `frontend/components/RecentMatches.tsx`, `frontend/components/travel/TrasferteExplorer.tsx` — usano `TeamCrest`.

Nessuna migrazione Alembic.

---

### Task 1: Backend — dizionario statico degli stemmi

**Files:**
- Create: `backend/app/core/crests.py`
- Test: `backend/tests/test_crests.py`

**Interfaces:**
- Produces: `CRESTS: dict[str, str]` (nome canonico → URL stemma) — usato da Task 2 e Task 3.

- [ ] **Step 1: scrivere il test che fallisce**

`backend/tests/test_crests.py`:

```python
from app.core.constants import TEAM_NAME
from app.core.crests import CRESTS


def test_juventus_crest_is_present():
    assert CRESTS[TEAM_NAME] == "https://crests.football-data.org/109.png"


def test_known_serie_a_club_crest_is_present():
    assert CRESTS["SSC Napoli"] == "https://crests.football-data.org/113.png"


def test_unknown_team_has_no_crest_entry():
    assert "Some Historic Club FC" not in CRESTS


def test_every_key_matches_a_canonical_stadiums_name_or_juventus():
    # Le chiavi devono restare allineate ai nomi canonici già usati altrove
    # (app/core/stadiums.py), altrimenti un lookup per nome squadra fallisce
    # silenziosamente in un posto e non nell'altro.
    from app.core.stadiums import STADIUMS

    known_names = set(STADIUMS.keys()) | {TEAM_NAME}
    assert set(CRESTS.keys()) <= known_names
```

- [ ] **Step 2: eseguire il test e verificare che fallisca**

Run: `cd backend && .venv/bin/pytest tests/test_crests.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.core.crests'` (il modulo non esiste ancora).

- [ ] **Step 3: creare il modulo**

`backend/app/core/crests.py`:

```python
"""Static reference data: team crest image URLs, keyed by the same canonical
names used throughout this codebase (see app.core.teams / app.core.stadiums).
Like stadiums.py, this doesn't change often enough to warrant a DB table or
an ingestion step.

URLs are football-data.org's own crest CDN (verified against a real,
read-only call to GET /v4/competitions/SA/teams — not guessed), one per
club that appeared in that response for the 2026-27 Serie A season.
Historic/relegated clubs not in the current season's roster (Empoli,
Cremonese, Salernitana, Spezia, Hellas Verona, Benevento, Brescia, SPAL,
Sampdoria) have no entry here — a lookup miss is expected and handled
gracefully by callers (no image shown), not an error.
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
```

- [ ] **Step 4: eseguire il test e verificare che passi**

Run: `cd backend && .venv/bin/pytest tests/test_crests.py -v`
Expected: PASS (tutti e 4 i test).

- [ ] **Step 5: lint**

Run: `cd backend && .venv/bin/ruff check app tests`
Expected: nessun errore.

- [ ] **Step 6: commit**

```bash
git add backend/app/core/crests.py backend/tests/test_crests.py
git commit -m "feat: add static team-crest URL lookup"
```

---

### Task 2: Backend — stemmi nelle risposte `/matches*`

**Files:**
- Modify: `backend/app/schemas/match.py`
- Modify: `backend/app/api/routes/matches.py`
- Test: `backend/tests/test_api_matches.py`

**Interfaces:**
- Consumes: `CRESTS` (Task 1).
- Produces: `MatchOut.home_crest_url: str | None`, `MatchOut.away_crest_url: str | None` — usati da Task 7/8 (frontend).

- [ ] **Step 1: scrivere il test che fallisce**

Aggiungere in fondo a `backend/tests/test_api_matches.py`:

```python
def test_list_matches_includes_crest_urls_for_known_teams(client, db):
    db.add(_make_match(external_id="crest-1", away_team="SSC Napoli"))
    db.commit()

    response = client.get("/api/v1/matches")
    match = response.json()["items"][0]

    assert match["home_crest_url"] == "https://crests.football-data.org/109.png"
    assert match["away_crest_url"] == "https://crests.football-data.org/113.png"


def test_list_matches_crest_url_is_null_for_unknown_team(client, db):
    db.add(_make_match(external_id="crest-2", away_team="Some Historic Club FC"))
    db.commit()

    response = client.get("/api/v1/matches")
    match = response.json()["items"][0]

    assert match["away_crest_url"] is None
```

- [ ] **Step 2: eseguire il test e verificare che fallisca**

Run: `cd backend && .venv/bin/pytest tests/test_api_matches.py -v -k crest`
Expected: FAIL — `KeyError: 'home_crest_url'` (il campo non esiste ancora nella risposta).

- [ ] **Step 3: aggiungere i campi allo schema**

In `backend/app/schemas/match.py`, in `MatchOut` dopo `is_approximate_date: bool = False`:

```python
    status: str
    result: str | None = None  # W/D/L from Juventus' perspective, None if not yet played
    is_approximate_date: bool = False
    home_crest_url: str | None = None
    away_crest_url: str | None = None
```

- [ ] **Step 4: valorizzarli in `match_to_out`**

In `backend/app/api/routes/matches.py`, aggiungere l'import in cima:

```python
from app.core.crests import CRESTS
```

E in `match_to_out`, dopo `is_approximate_date=m.source == SOURCE_WIKIPEDIA,`:

```python
def match_to_out(m: Match) -> MatchOut:
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
        home_crest_url=CRESTS.get(m.home_team),
        away_crest_url=CRESTS.get(m.away_team),
    )
```

- [ ] **Step 5: eseguire il test e verificare che passi**

Run: `cd backend && .venv/bin/pytest tests/test_api_matches.py -v`
Expected: PASS (tutti i test del file, non solo quelli nuovi).

- [ ] **Step 6: suite completa**

Run: `cd backend && .venv/bin/pytest -q`
Expected: PASS — `match_to_out` è condiviso da tutti gli endpoint `/matches*`, verifica che nessun altro test si rompa.

- [ ] **Step 7: commit**

```bash
git add backend/app/schemas/match.py backend/app/api/routes/matches.py backend/tests/test_api_matches.py
git commit -m "feat: include team crest URLs in match API responses"
```

---

### Task 3: Backend — stemma in `/travel/away-fixtures`

**Files:**
- Modify: `backend/app/schemas/travel.py`
- Modify: `backend/app/api/routes/travel.py`
- Test: `backend/tests/test_api_travel.py`

**Interfaces:**
- Consumes: `CRESTS` (Task 1).
- Produces: `AwayFixtureOut.crest_url: str | None` — usato da Task 7/8 (frontend).

- [ ] **Step 1: scrivere il test che fallisce**

Aggiungere in fondo a `backend/tests/test_api_travel.py`:

```python
def test_away_fixtures_includes_crest_url_for_known_opponent(client, db, monkeypatch):
    monkeypatch.setattr(
        travel_route.NominatimClient, "geocode", lambda self, q: (43.6158, 13.5189, "Ancona, Marche, Italia")
    )
    monkeypatch.setattr(travel_route.OsrmClient, "route", lambda self, *a: (300.0, 3.5))

    db.add(_away_match(external_id="crest-fixture", home_team="SSC Napoli"))
    db.commit()

    response = client.get("/api/v1/travel/away-fixtures", params={"from_city": "Ancona"})
    body = response.json()

    assert body["fixtures"][0]["crest_url"] == "https://crests.football-data.org/113.png"
```

- [ ] **Step 2: eseguire il test e verificare che fallisca**

Run: `cd backend && .venv/bin/pytest tests/test_api_travel.py -v -k crest`
Expected: FAIL — `KeyError: 'crest_url'`.

- [ ] **Step 3: aggiungere il campo allo schema**

In `backend/app/schemas/travel.py`, in `AwayFixtureOut` dopo `stadium_city: str | None`:

```python
class AwayFixtureOut(BaseModel):
    match_id: int
    opponent: str
    match_date: datetime
    competition: str
    stadium: str | None
    stadium_city: str | None
    crest_url: str | None
    distance_km: float | None
    duration_hours: float | None
    is_estimated: bool
    effort_score: float | None
    day_trip_feasible: bool | None
```

- [ ] **Step 4: valorizzarlo in `_build_fixture_out`**

In `backend/app/api/routes/travel.py`, aggiungere l'import:

```python
from app.core.crests import CRESTS
```

E in `_build_fixture_out`, nel dizionario `base` (l'opponent è sempre `match.home_team` in questo endpoint — vedi il commento esistente sulla query, filtrata per `Match.away_team == TEAM_NAME`):

```python
    base = dict(
        match_id=match.id,
        opponent=match.home_team,
        match_date=match.match_date,
        competition=match.competition,
        stadium=stadium_info.name if stadium_info else match.venue,
        stadium_city=stadium_info.city if stadium_info else None,
        crest_url=CRESTS.get(match.home_team),
    )
```

- [ ] **Step 5: eseguire il test e verificare che passi**

Run: `cd backend && .venv/bin/pytest tests/test_api_travel.py -v`
Expected: PASS.

- [ ] **Step 6: suite completa**

Run: `cd backend && .venv/bin/pytest -q`
Expected: PASS.

- [ ] **Step 7: commit**

```bash
git add backend/app/schemas/travel.py backend/app/api/routes/travel.py backend/tests/test_api_travel.py
git commit -m "feat: include opponent crest URL in away-fixtures API response"
```

---

### Task 4: Frontend — token CSS (`--ink`, `--stripe`, scala tipografica)

**Files:**
- Modify: `frontend/app/globals.css`

**Interfaces:**
- Produces: token `--ink`, `--stripe`, `--fs-display-1/2/3`, `--fs-body-1/2`, `--fs-label` — `--stripe` e la scala restano preparati per Fase B (hero, non ancora costruiti); `--ink` ha un consumo immediato in questo stesso task.

- [ ] **Step 1: aggiungere i token**

In `frontend/app/globals.css`, dentro `:root`, dopo il blocco `--win`/`--draw`/`--loss` esistente:

```css
  --win: #34c759;
  --draw: #ff9f0a;
  --loss: #ff453a;

  /* Numeri chiave: bianco puro, distinto da --text (usato per il body). */
  --ink: #f5f5f7;

  /* Pattern a strisce sottili per hero e separatori — introdotto qui,
     usato a partire da Sviluppo #2 Fase B (Composizione): nessun
     consumo in questo file finché l'hero non esiste. */
  --stripe: repeating-linear-gradient(
    90deg,
    rgba(245, 245, 247, 0.06) 0px,
    rgba(245, 245, 247, 0.06) 2px,
    transparent 2px,
    transparent 8px
  );

  /* Scala tipografica esplicita (Sviluppo #2 punto 3) — display per
     numeri/titoli hero (Fase B), body vicino all'attuale, label per le
     etichette maiuscole già in uso (es. .kpi-card__label). */
  --fs-display-1: 56px;
  --fs-display-2: 40px;
  --fs-display-3: 28px;
  --fs-body-1: 15px;
  --fs-body-2: 13px;
  --fs-label: 11px;
}
```

- [ ] **Step 2: applicare `--ink` a `.kpi-card__value`**

In `frontend/app/globals.css`, nella regola `.kpi-card__value` esistente:

```css
.kpi-card__value {
  font-size: 1.6rem;
  font-weight: 700;
  margin-top: 5px;
  letter-spacing: -0.01em;
  color: var(--ink);
}
```

- [ ] **Step 3: applicare `--fs-label` a `.kpi-card__label`**

Nella regola `.kpi-card__label` esistente, sostituire il valore hardcoded con il token (stesso valore, 0.72rem ≈ 11.52px, arrotondato a 11px — differenza visiva trascurabile, ora è un token riutilizzabile invece di un numero isolato):

```css
.kpi-card__label {
  font-size: var(--fs-label);
  color: var(--text-faint);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
```

- [ ] **Step 4: verifica**

Run: `cd frontend && npm run build`
Expected: build pulita (nessun errore, il CSS non è type-checked ma una sintassi rotta farebbe fallire comunque la build).

Verifica visiva: avviare `npm run dev`, aprire una pagina con KPI (es. `/`), confermare che i valori KPI sono leggermente più chiari/bianchi che prima (differenza sottile, `--ink` è quasi identico a `--text` di default ma ora è un token dedicato).

- [ ] **Step 5: commit**

```bash
git add frontend/app/globals.css
git commit -m "feat: add ink/stripe/typographic-scale CSS tokens"
```

---

### Task 5: Frontend — font display Oswald

**Files:**
- Modify: `frontend/app/layout.tsx`

**Interfaces:**
- Produces: variabile CSS `--font-display` (nome esatto scelto qui) applicata su `<html>` — consumata da Task 6 (monogramma) e, in Fase B, da hero/hero-numbers.

- [ ] **Step 1: verificare la documentazione Next 16 per `next/font`**

Prima di scrivere codice, leggere
`frontend/node_modules/next/dist/docs/01-app/03-api-reference/02-components/font.md`
(sezioni su `weight`, `variable`, "CSS variables") — Oswald non è una
variable font su Google Fonts, quindi serve specificare `weight` come
array esplicito, non un range. Confermare che il pattern qui sotto
corrisponde a quanto documentato prima di procedere; se diverge, adattare
il codice alla documentazione reale, non a questo piano.

- [ ] **Step 2: importare e configurare il font**

In `frontend/app/layout.tsx`, aggiungere l'import in cima (dopo gli import esistenti):

```tsx
import { Oswald } from "next/font/google";
```

Dopo gli import, prima di `export async function generateMetadata`:

```tsx
const oswald = Oswald({
  subsets: ["latin"],
  weight: ["600", "700"],
  variable: "--font-display",
  display: "swap",
});
```

- [ ] **Step 3: applicare la variabile su `<html>`**

Nel JSX di `RootLayout`, sull'elemento `<html>`:

```tsx
    <html lang={dict.htmlLang} className={oswald.variable}>
```

- [ ] **Step 4: verifica**

Run: `cd frontend && npm run build`
Expected: build pulita, nessun errore TypeScript o di risoluzione del font.

- [ ] **Step 5: commit**

```bash
git add frontend/app/layout.tsx
git commit -m "feat: self-host Oswald as the display font via next/font"
```

---

### Task 6: Frontend — brand "Juventum" e monogramma "JM"

**Files:**
- Modify: `frontend/app/layout.tsx`

**Interfaces:**
- Consumes: `--font-display` (Task 5).
- Produces: nessuna nuova interfaccia consumata da altri task.

- [ ] **Step 1: sostituire l'SVG del monogramma**

In `frontend/app/layout.tsx`, il blocco esistente:

```tsx
                <div className="sidebar__brand-mark">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M6 20V9.5L12 4l6 5.5V20"
                      stroke="#f5f5f7"
                      strokeWidth="1.6"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    <path
                      d="M10 20v-6h4v6"
                      stroke="var(--accent)"
                      strokeWidth="1.6"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
```

diventa:

```tsx
                <div className="sidebar__brand-mark">
                  <span
                    style={{
                      fontFamily: "var(--font-display)",
                      fontWeight: 700,
                      fontSize: "1.15rem",
                      letterSpacing: "-0.02em",
                      lineHeight: 1,
                    }}
                  >
                    <span style={{ color: "var(--ink)" }}>J</span>
                    <span style={{ color: "var(--accent)" }}>M</span>
                  </span>
                </div>
```

- [ ] **Step 2: aggiornare nome e sottotitolo del brand**

Nello stesso file, il blocco esistente:

```tsx
                <div className="sidebar__brand-text">
                  <span className="sidebar__brand-name">Momentum</span>
                  <span className="sidebar__brand-sub">JUVENTUS · JMI</span>
                </div>
```

diventa:

```tsx
                <div className="sidebar__brand-text">
                  <span className="sidebar__brand-name">Juventum</span>
                  <span className="sidebar__brand-sub">
                    {locale === "en" ? "Momentum Index · unofficial" : "Momentum Index · non ufficiale"}
                  </span>
                </div>
```

(`locale` è già disponibile nello scope di `RootLayout` da `const { locale, dict } = await getDictionary();` — nessun nuovo import necessario. Questo segue lo stesso pattern già usato in `generateMetadata` per la descrizione, non introduce nuove chiavi in `dictionaries.ts`.)

- [ ] **Step 3: verifica**

Run: `cd frontend && npm run build`
Expected: build pulita.

Verifica visiva: `npm run dev`, controllare che la sidebar mostri "JM" (J bianca, M oro) nel riquadro brand e "Juventum" / "Momentum Index · non ufficiale" come nome/sottotitolo, in entrambe le lingue (toggle IT/EN).

- [ ] **Step 4: commit**

```bash
git add frontend/app/layout.tsx
git commit -m "feat: rebrand sidebar as Juventum with JM monogram"
```

---

### Task 7: Frontend — componente `TeamCrest` e tipi

**Files:**
- Create: `frontend/components/TeamCrest.tsx`
- Modify: `frontend/lib/types.ts`

**Interfaces:**
- Consumes: `MatchOut.home_crest_url`/`away_crest_url` (Task 2), `AwayFixtureOut.crest_url` (Task 3).
- Produces: `TeamCrest({ url, name, size? }: { url: string | null; name: string; size?: number })` — componente React, usato da Task 8.

- [ ] **Step 1: aggiungere i campi ai tipi**

In `frontend/lib/types.ts`, in `MatchOut` dopo `is_approximate_date: boolean;`:

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
  home_crest_url: string | null;
  away_crest_url: string | null;
}
```

In `AwayFixtureOut`, dopo `stadium_city: string | null;`:

```ts
export interface AwayFixtureOut {
  match_id: number;
  opponent: string;
  match_date: string;
  competition: string;
  stadium: string | null;
  stadium_city: string | null;
  crest_url: string | null;
  distance_km: number | null;
  duration_hours: number | null;
  is_estimated: boolean;
  effort_score: number | null;
  day_trip_feasible: boolean | null;
}
```

- [ ] **Step 2: creare il componente**

`frontend/components/TeamCrest.tsx`:

```tsx
export function TeamCrest({ url, name, size = 18 }: { url: string | null; name: string; size?: number }) {
  if (!url) return null;

  return (
    // eslint-disable-next-line @next/next/no-img-element -- external, per-team crest URLs; not worth next/image's remote-pattern config for a small static set
    <img
      src={url}
      alt={name}
      width={size}
      height={size}
      style={{ objectFit: "contain", verticalAlign: "middle", marginRight: 6 }}
    />
  );
}
```

(Verificare durante l'implementazione se `next.config` consente `<img>` nativo senza avvisi ESLint diversi da quello già soppresso qui — se il progetto usa una regola diversa da `@next/next/no-img-element`, adattare il commento di soppressione a quella reale, non lasciare un avviso silenziato in modo sbagliato.)

- [ ] **Step 3: verifica tipo/build**

Run: `cd frontend && npm run build`
Expected: build pulita, nessun errore TypeScript.

- [ ] **Step 4: commit**

```bash
git add frontend/lib/types.ts frontend/components/TeamCrest.tsx
git commit -m "feat: add TeamCrest component and crest fields to frontend types"
```

---

### Task 8: Frontend — stemmi in tabella Matches, Ultime/Prossime partite, Trasferte

**Files:**
- Modify: `frontend/components/MatchTable.tsx`
- Modify: `frontend/components/UpcomingMatches.tsx`
- Modify: `frontend/components/RecentMatches.tsx`
- Modify: `frontend/components/travel/TrasferteExplorer.tsx`

**Interfaces:**
- Consumes: `TeamCrest` (Task 7), `MatchOut.home_crest_url`/`away_crest_url`, `AwayFixtureOut.crest_url`.
- Produces: nessuna nuova interfaccia consumata da altri task.

- [ ] **Step 1: `MatchTable.tsx`**

Aggiungere l'import:

```tsx
import { TeamCrest } from "./TeamCrest";
```

Le due celle esistenti:

```tsx
            <td>{m.home_team}</td>
            <td>{m.away_team}</td>
```

diventano:

```tsx
            <td>
              <TeamCrest url={m.home_crest_url} name={m.home_team} />
              {m.home_team}
            </td>
            <td>
              <TeamCrest url={m.away_crest_url} name={m.away_team} />
              {m.away_team}
            </td>
```

- [ ] **Step 2: `UpcomingMatches.tsx`**

Aggiungere l'import:

```tsx
import { TeamCrest } from "@/components/TeamCrest";
```

Nel blocco che mostra `vs {opponent}`, calcolare lo stemma dell'avversario e mostrarlo:

Sostituire l'intero blocco `{matches.map(...)}` con (unica riga cambiata: quella con `vs {opponent}`, tutto il resto identico all'originale):

```tsx
        {matches.map((m, i) => {
          const opponent = m.home_team === TEAM_NAME ? m.away_team : m.home_team;
          const opponentCrest = m.home_team === TEAM_NAME ? m.away_crest_url : m.home_crest_url;
          const homeAway = m.home_team === TEAM_NAME ? dict.common.home : dict.common.away;
          const { date, time } = formatDateTime(m.match_date, locale);
          return (
            <div
              key={m.id}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "12px 0",
                borderBottom: i < matches.length - 1 ? "1px solid var(--border)" : "none",
              }}
            >
              <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <span style={{ fontWeight: 600 }}>
                  <TeamCrest url={opponentCrest} name={opponent} />
                  vs {opponent}
                </span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  {m.competition} · {homeAway}
                </span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 2, textAlign: "right" }}>
                <span style={{ fontWeight: 600 }}>
                  {date} · {time}
                </span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  {m.venue ?? dict.upcomingMatches.venueTbd}
                </span>
              </div>
            </div>
          );
        })}
```

- [ ] **Step 3: `RecentMatches.tsx`**

Stessa modifica di Step 2, stesso pattern:

```tsx
import { TeamCrest } from "@/components/TeamCrest";
```

Sostituire l'intero blocco `{matches.map(...)}` con (unica riga cambiata: quella con `vs {opponent}`, tutto il resto identico all'originale):

```tsx
        {matches.map((m, i) => {
          const opponent = m.home_team === TEAM_NAME ? m.away_team : m.home_team;
          const opponentCrest = m.home_team === TEAM_NAME ? m.away_crest_url : m.home_crest_url;
          const homeAway = m.home_team === TEAM_NAME ? dict.common.home : dict.common.away;
          const score = `${m.home_goals ?? "-"}-${m.away_goals ?? "-"}`;
          return (
            <div
              key={m.id}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "12px 0",
                borderBottom: i < matches.length - 1 ? "1px solid var(--border)" : "none",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <ResultBadge result={m.result} />
                <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                  <span style={{ fontWeight: 600 }}>
                    <TeamCrest url={opponentCrest} name={opponent} />
                    vs {opponent}
                  </span>
                  <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                    {m.competition} · {homeAway}
                  </span>
                </div>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 2, textAlign: "right" }}>
                <span style={{ fontWeight: 600 }}>{score}</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  {formatDate(m.match_date, locale)}
                </span>
              </div>
            </div>
          );
        })}
```

- [ ] **Step 4: `TrasferteExplorer.tsx`**

Aggiungere l'import:

```tsx
import { TeamCrest } from "@/components/TeamCrest";
```

La cella esistente:

```tsx
                        <td>{f.opponent}</td>
```

diventa:

```tsx
                        <td>
                          <TeamCrest url={f.crest_url} name={f.opponent} />
                          {f.opponent}
                        </td>
```

- [ ] **Step 5: verifica tipo/build**

Run: `cd frontend && npm run build`
Expected: build pulita.

- [ ] **Step 6: verifica visiva**

Con backend e frontend avviati (DB locale con almeno una partita Juventus vs una squadra presente in `CRESTS`, es. SSC Napoli), aprire `/`, `/matches`, `/trasferte` e confermare che gli stemmi compaiono accanto ai nomi squadra dove noti, e che non c'è nulla di rotto (spazio vuoto pulito) dove lo stemma non è noto.

- [ ] **Step 7: commit**

```bash
git add frontend/components/MatchTable.tsx frontend/components/UpcomingMatches.tsx frontend/components/RecentMatches.tsx frontend/components/travel/TrasferteExplorer.tsx
git commit -m "feat: show team crests in matches table, upcoming/recent widgets, and trasferte"
```

---

## Copertura spec (tracciabilità)

| Punto spec | Coperto da |
|---|---|
| Monogramma "JM" | Task 6 |
| Tipografia Oswald | Task 5, consumata da Task 6 |
| Token `--ink`, `--stripe`, scala tipografica | Task 4 |
| Stemmi squadre (backend) | Task 1, 2, 3 |
| Stemmi squadre (frontend) | Task 7, 8 |

**Fuori scope per questo piano** (Fase B/C dello stesso Sviluppo #2): hero per pagina, KPI con sparkline/delta, grafici custom, motion, mobile-first, copy editoriale, finiture (favicon/manifest/OG/⌘K), accessibilità.
