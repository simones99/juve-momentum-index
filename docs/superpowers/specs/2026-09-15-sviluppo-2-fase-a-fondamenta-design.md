# Sviluppo #2, Fase A — Fondamenta: brand, tipografia, token, stemmi — Design

Data: 2026-09-15
Spec sorgente: `docs/analisi-prodotto-2026-09-09.md`, sezione "2. Identità
bianconera: design system premium" (gap G8-G13), sotto-scope "Fase A —
Fondamenta" concordato in sessione (Sviluppo #2 spezzato in tre fasi:
Fondamenta → Composizione → Rifinitura).

## Obiettivo

Aprire l'app e riconoscere in un secondo che è Juventus e che è curata,
senza logo ufficiale: un marchio proprio ("Juventum"), una tipografia
display coerente per numeri e titoli, i token CSS per sostenerla, e gli
stemmi reali delle squadre dove oggi c'è solo testo.

## Vincoli (dal documento prodotto, invariati)

- Tre colori: nero, bianco, oro (`--accent: #cdb079`). Nessun altro colore
  fuori da verde/arancio/rosso per gli esiti V/N/P.
- Nessun logo, wordmark o asset ufficiale Juventus. Bianco/nero/strisce
  sono linguaggio generico.
- Una sola famiglia di font aggiunta, nessuna nuova libreria UI.
- Ogni dato approssimato/mancante resta dichiarato in UI, mai nascosto
  silenziosamente (pattern `is_estimated`/`is_approximate` già in uso).
- Segue i pattern esistenti: modulo puro in `app/core/` per dati statici
  (vedi `stadiums.py`), schema Pydantic, nessuna migrazione se non serve.

## Decisioni prese in sessione

Confrontate con un mockup pubblicato (Artifact, monogramma + font display
sulla palette reale dell'app) prima di essere scelte:

1. **Monogramma**: wordmark "JM" condensato — "J" bianca + "M" oro,
   stessa famiglia scelta per i numeri (Oswald). Sostituisce l'attuale
   SVG a casetta nella sidebar (`frontend/app/layout.tsx`, dentro
   `.sidebar__brand-mark`).
2. **Font display**: Oswald (pesi 600/700), self-hosted via
   `next/font/google` (zero layout shift, come richiesto dalle linee
   guida trasversali del documento prodotto). Solo per numeri chiave e
   titoli — il testo body resta il font di sistema attuale
   (`-apple-system, BlinkMacSystemFont, ...`, invariato).
3. **Stemmi squadre**: dizionario statico in `app/core/`, stesso pattern
   di `stadiums.py` (nessuna tabella DB, nessuna migrazione), popolato
   con dati reali verificati in sessione (chiamata di sola lettura a
   `football-data.org/v4/competitions/SA/teams` con la chiave già
   configurata in `backend/.env`) — non URL inventati.

## Tipografia

- `next/font/google` import di Oswald, pesi `600` e `700`, in
  `frontend/app/layout.tsx` (o un modulo dedicato `frontend/lib/fonts.ts`
  se il piano preferisce isolarlo — decisione implementativa).
- Applicata via una classe/variabile CSS (es. `--font-display`) usata solo
  su: valore KPI (`.kpi-card__value`), monogramma sidebar, `<h1>` di
  pagina, numero Momentum Index, titoli hero (quando esisteranno in Fase
  B — qui si prepara solo il token, non gli hero stessi).
- `font-variant-numeric: tabular-nums` su tutte le colonne numeriche
  esistenti (tabella Matches: nessuna oggi ha cifre allineate a colonna
  fissa — verificare in implementazione dove si applica davvero, es.
  eventuali colonne di punteggio).
- **Verifica preliminare obbligatoria** (da `frontend/AGENTS.md`):
  controllare le API Next 16 per `next/font` in
  `frontend/node_modules/next/dist/docs/` prima di scrivere il codice —
  il pattern esatto (`variable`, `className`, uso in `<html>` vs singolo
  componente) va confermato lì, non assunto dalla memoria.

## Token CSS nuovi

In `frontend/app/globals.css`, dentro `:root` accanto ai token esistenti
(`--bg`, `--accent`, ecc.):

```css
--ink: #f5f5f7;      /* bianco puro, riservato ai numeri chiave */
--stripe: /* pattern strisce sottili, gradiente ripetuto nero/bianco a
             bassa opacità — valore esatto in fase di implementazione,
             per hero (Fase B) e separatori */
```

Scala tipografica esplicita (come classi utility o variabili, decisione
implementativa): display `56px/40px/28px`, body `15px/13px` (vicino
all'attuale, non un cambio drastico), label `11px` maiuscolo con
`letter-spacing` (il pattern esiste già per `.kpi-card__label`,
formalizzarlo come token riutilizzabile).

## Stemmi squadre

**File nuovo**: `backend/app/core/crests.py` — stesso pattern di
`backend/app/core/stadiums.py` (dict `frozen`, chiave = nome canonico
già usato in `app/core/teams.py`/`stadiums.py`):

```python
CRESTS: dict[str, str] = {
    "Juventus FC": "https://crests.football-data.org/109.png",
    "AC Milan": "https://crests.football-data.org/98.png",
    # ... vedi dati reali salvati in sessione
}
```

Dati reali per le 20 squadre di Serie A 2026-27 già verificati in
sessione (chiamata read-only all'API con la chiave esistente), salvati
in `/private/tmp/claude-501/-Users-simonemezzabotta-Coding-Projects-juventum/d175fbcb-e12e-4f21-b708-612d439d1339/scratchpad/serie-a-crests-2026-09-15.json`
— il piano d'implementazione li userà direttamente (nessuna nuova
chiamata API necessaria per questi 20). Squadre storiche/retrocesse
(Empoli, Cremonese, Salernitana, Spezia, Hellas Verona, Benevento,
Brescia, SPAL, Sampdoria — assenti dalla stagione corrente) restano
senza stemma: lookup che ritorna `None`, UI che omette l'immagine senza
rompersi (stesso pattern di dato mancante dichiarato, non nascosto).

**Backend — schema**: `MatchOut` (`backend/app/schemas/match.py`)
guadagna `home_crest_url: str | None` e `away_crest_url: str | None`;
`AwayFixtureOut` (`backend/app/schemas/travel.py`) guadagna
`crest_url: str | None` per la squadra di casa (Juventus in trasferta,
l'avversario è sempre l'altra squadra — verificare in implementazione
quale lato serve davvero). Valorizzati nelle route (`matches.py`,
`travel.py`) con un lookup su `CRESTS.get(nome_canonico)`.

**Frontend**: `MatchTable.tsx`, `UpcomingMatches.tsx`,
`RecentMatches.tsx`, componenti Trasferte mostrano lo stemma quando
presente (immagine piccola accanto al nome squadra), nulla quando
`None`.

## File coinvolti (riepilogo)

Backend:
- Create: `backend/app/core/crests.py`
- Modify: `backend/app/schemas/match.py`, `backend/app/schemas/travel.py`
- Modify: `backend/app/api/routes/matches.py`, `backend/app/api/routes/travel.py`
- Test: nuovo test puro per `crests.py`, estensione test API esistenti

Frontend:
- Modify: `frontend/app/layout.tsx` (monogramma, font setup)
- Modify: `frontend/app/globals.css` (token nuovi)
- Modify: `frontend/lib/types.ts` (nuovi campi crest nei tipi)
- Modify: `frontend/components/MatchTable.tsx`,
  `frontend/components/UpcomingMatches.tsx`,
  `frontend/components/RecentMatches.tsx`, componenti Trasferte

Nessuna migrazione Alembic — `crests.py` è statico come `stadiums.py`.

## Test

- Backend: test puro su `crests.py` (lookup nome canonico noto → URL
  atteso; nome sconosciuto → `None`); estensione dei test API esistenti
  (`test_api_matches.py`, `test_api_travel.py`) per verificare che
  `*_crest_url` sia popolato quando la squadra è nota e `None` quando
  non lo è.
- Frontend: nessuna suite automatica esiste ancora per i componenti
  (gap noto, non in scope qui — coperto da Sviluppo #10). Verifica
  manuale: `npm run build` pulito, controllo visivo che gli stemmi
  compaiano nelle pagine coinvolte con backend/DB locale avviati.

## Fuori scope per Fase A

Rimandato a Fase B (Composizione) o Fase C (Rifinitura) dello stesso
Sviluppo #2: hero per pagina, KPI con delta/sparkline, grafici con
tooltip/legenda/annotazioni custom, motion (transizioni, hover, badge
LIVE pulsante), mobile-first (bottom tab bar), riscrittura copy in
`dictionaries.ts`, finiture (favicon/manifest/OG/`⌘K`), accessibilità
(righe tabella come link veri, focus ring, contrasto).

## Insidie

- `next/font` con Oswald richiede la verifica preliminare dei doc Next
  16 (vedi sopra) — non assumere la sintassi da progetti precedenti.
- Il pattern strisce (`--stripe`) è preparato qui come token ma il suo
  uso reale (hero) arriva in Fase B: il valore esatto del gradiente va
  scelto guardando dove verrà applicato per la prima volta, per non
  indovinare un'opacità/spaziatura sbagliata in astratto.
- Gli stemmi mancanti per squadre storiche non sono un blocco: il
  fallback grazioso è parte del design, non un TODO lasciato aperto.
