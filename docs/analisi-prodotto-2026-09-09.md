# Analisi prodotto e roadmap "premium" — Juventum

Data: 2026-09-09
Scopo: fotografare lo stato reale dell'app, elencare i gap che la tengono
"progetto personale" e indicare come colmarli per farla sembrare un prodotto
caro, curato e in pieno stile bianconero.

Pubblico dichiarato: **l'autore e qualche amico**. Questo orienta le scelte:
niente account, niente moderazione, niente scala; sì a cura, velocità,
telefono in tasca il sabato, e a un modello di cui ci si può fidare.

## Metodo

- Letto per intero backend (`app/`, `tests/`, `scripts/`, migrazioni),
  frontend (`app/`, `components/`, `lib/`, `globals.css`), README, `docs/`,
  CI, docker-compose, script launchd e i due piani in `~/.claude/plans/`.
- Interrogato il Postgres locale (Homebrew, porta 5432) usato dai server di
  sviluppo.
- Letto `logs/scheduled-ingest.log` e lo stato di `launchctl`.
- Avviato backend e frontend in locale e fotografato le sei pagine con Brave
  headless a 1440×1000 (Chrome/Playwright non installati sul Mac).

## Stato attuale in sintesi

Il progetto ha sei giorni di vita (primo commit 2026-09-03) e 21 commit. La
base ingegneristica è già seria, e va detto chiaramente:

- FastAPI + SQLAlchemy + Alembic, 132 test verdi, `ruff`, CI con Postgres di
  servizio, Docker per backend e ingest.
- Elo calcolato su **tutta la Serie A** (2.280 partite, 20 squadre/stagione),
  non solo sulle partite Juve; probabilità 1/X/2 **backtestate** con
  cross-validation leave-one-season-out e documentate con onestà in
  `docs/backtest.md`.
- Live poller, notifiche Web Push (tre eventi), pronostici "Batti il modello"
  con streak e statistiche community, Trasferte con routing OSRM reale,
  i18n IT/EN completa, design "Liquid Glass" scuro con accento oro.

La parte "skills" è visibile a chi legge il codice. Quello che manca è che
sia visibile **a chi apre l'app**: oggi la maggior parte delle pagine è vuota
o mostra dati segnaposto, e l'estetica è corretta ma anonima.

## Gap rilevati (con evidenze)

### 1. Dati e operatività

**G1. L'app gira su dati stantii e segnaposto.** Il DB locale contiene
2.280 partite, tutte `source='wikipedia'`, tutte `FINISHED`, con la data
placeholder di inizio stagione (15 agosto). Stagioni 2019-20 → 2024-25:
manca l'intera 2025-26 e la 2026-27 in corso. Zero partite future.
Conseguenze visibili: "Prossime partite" vuota, sidebar "Nessuna partita in
programma", Trasferte inutilizzabile, Pronostici senza partite su cui
pronosticare, tabelle con "15 ago 2024" ripetuto su ogni riga, grafici con
l'asse X che ripete la stessa data, Match Brief senza avversario e senza
probabilità. Quattro pagine su sei non hanno nulla da mostrare.

**G2. La chiave football-data.org è configurata ma mai usata sul DB di
sviluppo.** `backend/.env` ha `FOOTBALL_DATA_API_KEY` valorizzata; il DB
non ha nemmeno una riga `source='football-data'`.

**G3. Il refresh giornaliero è rotto, e lo è per un'immagine Docker
vecchia.** `logs/scheduled-ingest.log`: run del 4 settembre uscita 0; run
del 9 settembre alle 10:23 uscita 1 con `HTTPStatusError 403` su
`SA season=2022` (stagione fuori dalla finestra del free tier). Il
traceback cita `ingest.py` riga 43 e `football_data_client.py` riga 93 con
`raise_for_status()` non intercettato: è **codice precedente** al commit
`4a43de1` ("never crash the run on one bad season"), che oggi su `main`
converte il 403 in `FootballDataError` e prosegue. Causa:
`scripts/scheduled_ingest.sh` fa `docker compose run --rm ingest` senza
`--build`, quindi la fix esiste nel repo ma non gira mai.

**G4. Due database che divergono.** Il job launchd scrive sul Postgres del
container `db` (volume `pgdata`); i server di sviluppo con `backend/.env`
leggono `localhost:5432`, che quando Docker è spento è il Postgres Homebrew.
Stessa porta, dati diversi. Non ho potuto verificare il contenuto del DB
Docker perché il daemon non rispondeva.

**G5. Il live poll locale non è attivo.** `launchctl list` mostra solo
`com.juventum.scheduled-ingest`; nessun `logs/scheduled-live-poll.log`;
`ADMIN_TOKEN` vuoto in `backend/.env`, quindi `/admin/poll-live`
risponderebbe comunque 404. Live Matchday Mode, kickoff push e risoluzione
pronostici oggi non possono scattare.

**G6. Nessun deploy.** README con `<link Vercel qui dopo il deploy>` e
`<link Render qui dopo il deploy>`; `docs/screenshots/overview.png`
referenziato ma la cartella non esiste. Finché non è online, per gli amici
non esiste.

**G7. Backtest "definitivo" mai completato.** `docs/backtest.md` termina con
la sezione "Elo completo con date reali — TBD". Le costanti in
`win_probability.py` (0.28/400) sono ancora quelle tarate sull'Elo parziale;
il dato intermedio suggeriva 0.30/300.

### 2. Design e percezione "premium"

**G8. Identità generica.** Il look è "dashboard Apple scura": ben eseguito
(vetro, raggi ampi, oro `#cdb079`), ma non racconta la Juventus. Brand in
sidebar: "Momentum / JUVENTUS · JMI". Nessun monogramma, nessuna striscia,
nessuno stemma degli avversari, nessuna tipografia display per i numeri. Il
nome "Juventum" (cartella, compose, launchd) è più forte e non compare mai
nell'interfaccia.

**G9. Mancano i segnali base di un prodotto finito.** `frontend/public/`
contiene solo `sw.js`: nessuna favicon, nessuna icona, nessun manifest,
nessuna OG image. Il tab del browser mostra l'icona di default.

**G10. Empty state e copy da log di sviluppo.** "Nessuna partita in
programma nel dataset al momento", "Anteprima basata sulle ultime partite",
badge "AI-enhanced"/"Template". Un prodotto caro parla come una rivista, non
come un README.

**G11. Nessuna gestione del tempo di attesa.** Nessun `loading.tsx`,
`error.tsx` o `not-found.tsx`; tutte le fetch sono `cache: "no-store"`
(`frontend/lib/api.ts`). Con il cold start di Render (30-60 s) l'utente vede
una pagina bianca; in `/brief/next` la pagina aspetta anche la chiamata LLM
(timeout 8 s) prima di renderizzare.

**G12. KPI e grafici senza contesto e senza motion.** Card con un numero
secco (98.7, 25.0, 12, 2W) senza confronto, delta o sparkline. Grafici
Recharts con tooltip e legenda di default. Nessuna animazione di ingresso,
nessun conteggio, nessuna transizione. Tabelle con righe cliccabili via
`onClick` ma non raggiungibili da tastiera, senza stati di focus.

**G13. Mobile trattato come ripiego.** Sotto 860 px la sidebar si
schiaccia in una riga di pill e il widget "prossima partita" sparisce;
le tabelle restano tabelle. Per un uso "sabato sul telefono" serve un layout
pensato mobile-first.

### 3. Prodotto

**G14. L'asset più grande è nascosto.** Il DB ha l'Elo di tutte le venti
squadre per sei stagioni, ma nessuna pagina lo mostra. Niente classifica
Elo, niente profilo avversario, niente "dove sta la Juve rispetto alla
lega". Le probabilità del brief restano un numero inspiegato.

**G15. La pagina partita è vuota di significato.** `/matches/[id]` mostra
solo il brief post-partita; per una partita futura mostra "non ancora
giocata". Non c'è un luogo unico dove vivere la partita prima, durante e
dopo.

**G16. Il Match Brief è una riscrittura di quattro righe.** L'LLM riceve le
righe template e le riformula; niente sezioni, niente chiave tattica, niente
avversario. Viene rigenerato a ogni richiesta (costo e latenza) e non è mai
persistito.

**G17. Notifiche minimali.** `sw.js` mostra titolo e corpo senza icona,
immagine o azioni; il click apre sempre `/`. Il frontend registra la
subscription con `device_id: null`, quindi nessuna notifica può essere
personalizzata ("hai battuto il modello"). Mancano gli eventi che contano di
più: gol, fischio finale, pronostico risolto. Lo swing di momentum può
ri-notificare a ogni ingest (documentato in `ingest.py`, non risolto).

**G18. Non installabile.** Senza manifest la PWA non si aggiunge alla home
del telefono, che per un'app da tifoso è il gesto che la rende "propria".

**G19. Pronostici essenziali.** Solo 1/X/2, nessun risultato esatto,
nessuna classifica tra amici, nessun modo di condividere il risultato su
WhatsApp.

### 4. Modello

**G20. Il Momentum Index si riscrive da solo.** `momentum_index.py`
normalizza min-max `elo_after`, `points_rolling5` e `goal_diff_rolling5`
sull'**intera** serie storica. Ogni nuovo massimo o minimo ricalibra
retroattivamente tutti i valori passati: il 65.7 di oggi può diventare 61
domani senza che sia successo nulla. Per un indice che si vuole "seguire nel
tempo" è un difetto strutturale, oltre che una domanda scomoda in
un'intervista.

**G21. Elo senza margine di vittoria né regressione stagionale.** K fisso
20, vantaggio casa 65 scelto a mano, nessun peso al 4-0 rispetto all'1-0,
nessuna regressione verso la media a inizio stagione. Sono le tre
estensioni standard (ClubElo, FiveThirtyEight) e sono tutte misurabili con
il backtest già scritto.

**G22. Probabilità live dichiaratamente non calibrate.**
`adjust_live_probabilities` sposta massa a mano per gol di differenza senza
tenere conto del tempo residuo (l'API free non dà il minuto). È onesto ed è
etichettato, ma resta il punto più debole del "Live".

### 5. Qualità tecnica

**G23. Frontend senza test.** Nessun Vitest, nessun Playwright; CI frontend
= lint + build. Tutta la logica di formattazione, i18n e polling è
scoperta.

**G24. Nessuna osservabilità.** Niente Sentry, niente log strutturati,
`/healthz` non dice quando sono stati aggiornati i dati.

**G25. Piccole inefficienze che diventeranno visibili.**
`GET /matches` carica tutte le righe Juve e pagina/filtra in Python;
`LiveMatchBanner` interroga `/matches/live` ogni 35 s da ogni client aperto,
anche nei giorni senza partita; il layout chiama `/matches/upcoming` a ogni
render di ogni pagina.

## Vincoli e assunzioni

- Free tier ovunque: Render (spin-down), Neon, football-data.org (10
  req/min, finestra di ~4 stagioni), OSRM demo, Nominatim (1 req/s),
  OpenRouter a consumo. Nessuna spesa fissa.
- Nessun account utente: identità = cookie `device_id` (già in
  `frontend/proxy.ts`), eventualmente un nickname scelto.
- Italiano prima, inglese mantenuto.
- Marchi: nessun uso del logo "J" ufficiale, del wordmark o di asset
  Juventus. Il disclaimer "non affiliato" resta. Bianco, nero, strisce e oro
  sono linguaggio generico e vanno bene.

## I 10 sviluppi

| # | Sviluppo | Importanza | Effort | Gap coperti |
|---|---|---|---|---|
| 1 | Dati vivi e messa in produzione | Critica | S-M | G1-G7 |
| 2 | Identità bianconera: design system premium | Alta | L | G8-G13 |
| 3 | Classifica Elo Serie A e profili avversario | Alta | M | G14 |
| 4 | Matchday Hub con timeline delle probabilità live | Alta | M-L | G15, G22 |
| 5 | Modello v2 e Model Card pubblica | Alta | M | G20, G21, G7 |
| 6 | Match Brief editoriale v2 | Alta | M | G16, G11 |
| 7 | PWA installabile e notifiche ricche | Media-Alta | S | G17, G18 |
| 8 | Pronostici v2: risultato esatto, classifica amici, card | Media-Alta | M-L | G19 |
| 9 | La stagione in un colpo d'occhio | Media | M | G12, G14 |
| 10 | Velocità percepita, affidabilità, osservabilità | Media | S-M | G11, G23-G25 |

Effort indicativo a persona singola: S = 1-2 giorni, M = 3-5, L = 6-10.

---

### 1. Dati vivi e messa in produzione

**Obiettivo.** Ogni pagina mostra la stagione in corso con date, orari e
stadi veri; i dati si aggiornano da soli senza il Mac acceso; l'app ha un
URL da mandare agli amici.

**Cosa c'è già da riusare.** Client API con throttling e gestione quota;
regola mono-sorgente per stagione (le righe Wikipedia vengono sostituite
quando l'API riesce); `default_seasons()` che calcola da sola
2023-24 → 2026-27; `scripts/check_team_names.py` per gli alias; endpoint
`/admin/refresh` e `/admin/poll-live`; `SUPPORTED_COMPETITIONS` include già
la Champions League.

**Linee guida.**

1. *Una sola verità sui dati in locale.* Decidere che il DB di sviluppo è il
   Postgres Homebrew (o quello Docker, ma uno solo) e scriverlo nel README.
   Se resta il cron locale: `docker compose run --build --rm ingest` in
   `scheduled_ingest.sh`. Meglio ancora: dismettere il cron locale appena
   esiste quello cloud (punto 4).
2. *Prima ingestione reale.* `python -m app.ingestion.ingest` con la chiave
   vera; attesi ~4 stagioni via API (2023-24 → 2026-27) e le più vecchie in
   fallback Wikipedia. Subito dopo `scripts/check_team_names.py`: ogni nome
   non mappato va aggiunto a `app/core/teams.py`, altrimenti la storia Elo
   di quel club si spezza in due (era il rischio #1 del piano Fase 2, mai
   chiuso con la chiave vera).
3. *Stadi.* Gli avversari di Champions non sono in `stadiums.py`: la UI li
   mostra già senza distanza, comportamento corretto. Aggiungere una
   decina di stadi europei solo se si vuole la "trasferta europea" in
   Trasferte.
4. *Refresh in cloud senza Docker e senza Mac.* Un workflow GitHub Actions
   con `schedule: cron "0 2 * * *"` che fa checkout del repo, installa
   `requirements.txt`, e lancia `python -m app.ingestion.ingest` con
   `DATABASE_URL` (Neon, connection string diretta) e
   `FOOTBALL_DATA_API_KEY` come secret. Vantaggi: gira sempre il codice di
   `main`, niente immagine da ricostruire, log su GitHub. Evitare di
   affidare l'ingest completo a `POST /admin/refresh` su Render free: il
   run dura oltre un minuto e l'HTTP può cadere.
5. *Live poll in cloud.* GitHub Actions ha una granularità minima di 5
   minuti e orari imprecisi. Usare un servizio tipo cron-job.org (gratuito,
   fino a 1 minuto) che chiama `POST /admin/poll-live` con `X-Admin-Token`
   ogni 2-3 minuti. Nei giorni senza partita costa una query. Lo stesso
   servizio può fare da warm-up per Render (vedi punto 10).
6. *Deploy.* Seguire la sezione README: Neon → Render (Dockerfile,
   `/healthz`, tutte le env inclusi VAPID e `ADMIN_TOKEN`) → Vercel con
   `NEXT_PUBLIC_API_BASE_URL` e `NEXT_PUBLIC_VAPID_PUBLIC_KEY`. Poi
   sostituire i placeholder del README e aggiungere `docs/screenshots/`.
7. *Freschezza visibile.* Tabella `ingest_runs (started_at, finished_at,
   status, matches_upserted, source_summary)` scritta da `update_matches`;
   `/healthz` espone `last_successful_ingest_at`; il footer mostra "Dati
   aggiornati alle 03:12". È il primo segnale di fiducia per chi apre
   l'app.
8. *Chiudere il backtest.* Dopo l'ingestione con date reali, rilanciare
   `scripts/backtest_win_probability.py`, compilare la sezione TBD di
   `docs/backtest.md` e, se il miglioramento è confermato, aggiornare le
   costanti in `win_probability.py` in un commit dedicato.

**Insidie.** Il free tier può negare stagioni oltre la finestra (403):
già gestito su `main`. L'API usa nomi diversi da Wikipedia: il passo 2 è
obbligatorio prima di fidarsi dei grafici. Le date Wikipedia delle stagioni
vecchie restano placeholder: dichiararlo in UI (badge "date approssimate"
sulle stagioni ≤ 2022-23) invece di nasconderlo.

**Fatto quando.** Overview mostra le prossime 5 partite con orario e
stadio; il footer riporta un orario di aggiornamento di oggi; il link nel
README apre l'app; il workflow cron ha almeno un run verde.

---

### 2. Identità bianconera: design system premium

**Obiettivo.** Aprire l'app e capire in un secondo che è Juventus e che è
stata fatta con cura: contrasto netto, un solo accento oro, numeri grandi e
belli, movimento discreto, copy editoriale.

**Cosa c'è già.** Token CSS in `globals.css` (già bianco/nero/oro), shell
con sidebar vetro, componenti piccoli e puliti, i18n centralizzata in
`dictionaries.ts` (cambiare il tono dei testi è un solo file).

**Linee guida.**

1. *Nome e marchio.* Brand "Juventum" in sidebar e in `<title>`; sottotitolo
   "Momentum Index · non ufficiale". Monogramma originale: una "J" o
   "JM" costruita da tre strisce verticali, o un semplice quadrato
   bianco/nero. Mai il logo ufficiale.
2. *Tipografia.* Tenere il font di sistema per il testo, aggiungere **una**
   famiglia display per numeri e titoli via `next/font` (self-hosted, zero
   layout shift): una grottesca condensata (Barlow Condensed, Sofia Sans
   Condensed, Oswald) oppure una geometrica decisa (Space Grotesk). Numeri
   tabulari (`font-variant-numeric: tabular-nums`) ovunque ci siano
   colonne.
3. *Token.* Aggiungere `--ink` (bianco puro per i numeri chiave),
   `--stripe` (pattern a strisce sottili per hero e separatori), scala
   tipografica esplicita (display 56/40/28, body 15/13, label 11 maiuscolo
   con tracking). Tema scuro come default "nero Juve"; un tema chiaro
   "bianco" è un plus, non un requisito.
4. *Stemmi.* L'API football-data v4 fornisce `homeTeam.crest` e
   `awayTeam.crest`. Introdurre una tabella `teams (name, short_name, tla,
   crest_url)` popolata dall'ingestione, oppure una colonna in
   `app/core/teams.py` come ponte. Mostrare gli stemmi in Ultime/Prossime
   partite, tabella Matches, Momentum Details, Trasferte. È il singolo
   dettaglio che fa più "prodotto vero".
5. *Hero per pagina.* Ogni pagina apre con un blocco alto: titolo display,
   una frase, e un numero protagonista (Overview: Momentum attuale con
   delta rispetto a 5 partite fa; Matches: record stagionale V-N-P; Brief:
   avversario con stemma e countdown).
6. *KPI con contesto.* Ogni card: valore, delta con freccia e colore,
   sparkline delle ultime 10 partite, etichetta breve. I numeri entrano con
   un conteggio (rAF, 600 ms, `prefers-reduced-motion` rispettato).
7. *Grafici.* Tooltip custom (componente React, non `contentStyle`),
   legenda propria, gradiente più deciso, punti evidenziati solo su hover,
   annotazioni per i momenti chiave (vedi punto 9), asse X con tick
   diradati e formattati per stagione. `isAnimationActive` con easing
   breve.
8. *Motion.* Transizioni di pagina con fade/slide di 150-200 ms
   (`View Transitions` di Next o CSS), hover sulle card con sollevamento di
   1-2 px, badge "LIVE" con pulsazione. Poco, coerente, sempre disattivabile.
9. *Mobile-first.* Sotto 860 px: bottom tab bar con 5 icone, hero
   compresso, tabelle che diventano liste di card (già lo stile di
   `RecentMatches`), sidebar widget "prossima partita" spostato in cima.
10. *Copy.* Riscrivere `dictionaries.ts` con tono da programma di
    matchday: "Il calendario arriva a giorni", "Prossima sfida: Napoli,
    sabato 20:45, Allianz Stadium", "Brief scritto con l'aiuto di un
    modello linguistico" invece di "AI-enhanced". Empty state con
    un'azione, non un vicolo cieco.
11. *Finiture.* `app/icon.tsx` (favicon generata), `app/apple-icon.tsx`,
    `app/opengraph-image.tsx` (OG dinamica: "Juventus 62.4 · momentum in
    crescita"), `metadataBase`, palette comandi ⌘K per saltare a
    stagioni, avversari, partite (leggera: un dialog con lista
    filtrabile, nessuna libreria pesante).
12. *Accessibilità.* Righe tabella come link veri (`<a>` nella prima cella
    o `<tr>` con `role="link"` e `tabIndex`), focus ring oro visibile,
    contrasto ≥ 4.5:1 sui testi muted (oggi `--text-faint` a 36% è sotto
    soglia su molte etichette).

**Insidie.** Il glass con `backdrop-filter` costa su mobile: ridurre il
blur sotto 860 px. Nessuna libreria UI da aggiungere; il CSS attuale basta.
Verificare le API Next 16 in `node_modules/next/dist/docs/` come richiesto
da `frontend/AGENTS.md` prima di usare icone, manifest e OG file-based.

**Fatto quando.** Screenshot a 1440 e 390 px senza empty state, con stemmi,
hero, KPI con delta e favicon; Lighthouse Accessibility ≥ 95.

---

### 3. Classifica Elo Serie A e profili avversario

**Obiettivo.** Rendere visibile l'Elo dell'intera lega, che è già nel DB, e
dare a ogni avversario una pagina. Le probabilità del brief diventano
spiegabili.

**Cosa c'è già.** `elo_ratings` con `elo_before/elo_after` per ogni squadra
in ogni partita; `app/core/teams.py` con nomi canonici; `stadiums.py`;
`_head_to_head` in `template_brief.py`; Trasferte per la distanza.

**Linee guida.**

1. *Backend.* `GET /api/v1/elo/standings?season=`: per ogni squadra della
   stagione, ultimo `elo_after`, variazione rispetto alla giornata
   precedente, posizione, e posizione della Juve con gap dalla vetta. Query
   con `row_number() over (partition by team order by rating_date desc,
   match_id desc)`. `GET /api/v1/elo/history?season=&teams=`: serie per
   bump chart (rank per giornata) limitata a 20 squadre. `GET
   /api/v1/teams/{slug}`: Elo attuale e storico, precedenti con la Juve
   con punteggi, stadio, prossima sfida, forma ultime 5.
2. *Slug.* Derivato dal nome canonico in `teams.py` (`ssc-napoli`), unico
   posto dove vive l'identità.
3. *Frontend.* Pagina `/classifica` (voce sidebar "Potere"): tabella con
   stemma, rating, delta con freccia, mini-sparkline; bump chart della
   stagione con la Juve evidenziata in oro e le altre in grigio. Pagina
   `/avversari/[slug]`: hero con stemma, Elo e rank, storico Elo vs Juve
   sovrapposti, lista precedenti, card stadio con distanza dalla città
   salvata (riuso di `getAwayFixtures`), link alla prossima sfida.
4. *Spiegabilità.* Nel brief e nel Matchday Hub: "Juve 58%: 1.712 Elo
   contro 1.664, 3ª in classifica Elo, vantaggio casa +65".

**Insidie.** Il "delta ultima giornata" ha senso solo con date reali:
sulle stagioni Wikipedia mostrare "n/d". Le squadre di Champions non
italiane vanno filtrate dalla classifica di Serie A (filtrare per
`competition_code='SA'` nella stagione).

**Fatto quando.** La classifica mostra 20 squadre con stemma e delta;
ogni avversario in tabella Matches è un link alla sua pagina.

---

### 4. Matchday Hub con timeline delle probabilità live

**Obiettivo.** Una pagina per partita che cambia con il tempo: prima,
durante, dopo. È la pagina che si apre il sabato.

**Cosa c'è già.** `poll_live_matches` ogni ~2,5 min; `/matches/live`;
`adjust_live_probabilities`; `LiveMatchBanner`; `PredictionForm`; brief
pre e post; Trasferte.

**Linee guida.**

1. *Stato.* `/partita/[id]` (o evoluzione di `/matches/[id]`) con tre
   viste in base a `status`: `SCHEDULED/TIMED` → pre; `IN_PLAY/PAUSED` →
   live; `FINISHED` → post. Il banner live diventa un link a questa
   pagina.
2. *Pre.* Hero con stemmi e countdown (client component), probabilità con
   spiegazione, brief pre, form pronostico, split della community per
   quella partita (`GET /predictions/split?match_id=`: conteggio per
   esito, senza identità), card trasferta se fuori casa.
3. *Live.* Nuova tabella `live_snapshots (match_id, taken_at, status,
   home_goals, away_goals, p_win, p_draw, p_loss)` scritta dal poller a
   ogni giro mentre la partita è live (~40 punti a partita). Grafico
   "probabilità di vittoria nel tempo" come step area con i gol marcati;
   polling client ogni 30 s solo su questa pagina.
4. *Post.* Risultato, delta Elo, brief post, "il modello dava questo
   esito al 31%", stato del proprio pronostico e della community,
   momento migliore/peggiore della timeline.
5. *Fine partita.* Sul passaggio a `FINISHED` il poller lancia
   `recompute_all_derived` e `resolve_predictions` subito (pochi secondi a
   questa scala), così la pagina post è pronta al fischio finale e non alle
   3 di notte.

**Insidie.** L'API free non dà il minuto: la timeline usa l'orario del
poll, dichiarandolo. Render free può addormentarsi durante la partita: il
warm-up del punto 10 è un prerequisito del live.

**Fatto quando.** Una partita reale attraversa i tre stati senza
intervento manuale e la timeline ha punti per tutti i 90 minuti.

---

### 5. Modello v2 e Model Card pubblica

**Obiettivo.** Un indice stabile, un Elo più fedele, probabilità calibrate,
e una pagina che mostra tutto questo con i numeri veri. La trasparenza è un
tratto da prodotto caro e un biglietto da visita tecnico.

**Cosa c'è già.** `compute_elo_history` pura e testata;
`scripts/backtest_win_probability.py` con CV leave-one-season-out;
`docs/backtest.md` come registro storico.

**Linee guida.**

1. *Momentum su scala fissa (versione 2).* Sostituire i tre min-max con
   scale interpretabili: Elo → `clip((elo - 1400) / 500) * 100` o una
   logistica centrata sulla media di lega; punti → `points_rolling5 / 3 *
   100` (scala naturale 0-3); differenza reti → `clip((gd5 + 2) / 4) *
   100`. Aggiungere `momentum_version` in `juve_momentum` e un test che
   dimostra che aggiungere una partita non cambia i valori passati.
   Mostrare in Momentum Details la scomposizione (quanto viene da Elo,
   punti, reti).
2. *Elo con margine di vittoria.* Moltiplicatore sul K in stile
   FiveThirtyEight: `ln(|gd| + 1) * 2.2 / (0.001 * diff_vincitore + 2.2)`.
   Regressione a inizio stagione: `1500 + (elo - 1500) * 2/3`. Vantaggio
   casa e K stimati con grid search nella stessa CV. Ogni variante è una
   riga nel backtest: si adotta solo ciò che migliora il log loss medio.
3. *Calibrazione.* Con 228 partite Juve evitare modelli ricchi: un
   temperature scaling a un parametro sul logit dell'Elo, o Platt a due,
   fittato in CV. Reliability diagram prima/dopo nel doc.
4. *Model Card in app.* Pagina `/modello`: come funziona in tre paragrafi,
   log loss/Brier contro le baseline, tabella di calibrazione, limiti
   dichiarati, data dell'ultimo backtest. I numeri vengono da un
   `docs/backtest.json` generato dallo script, non calcolati a runtime.
5. *Backtest in CI.* Fixture congelata (`tests/fixtures/juve_matches.csv`
   con Elo pre-partita di entrambe le squadre) e un test che fallisce se il
   log loss supera una soglia: il modello non può peggiorare senza che
   qualcuno se ne accorga.

**Insidie.** K e vantaggio casa alimentano anche il Momentum: cambiarli
cambia i grafici. Farlo una volta, con `momentum_version` e una nota nel
changelog. Non tarare due volte sullo stesso rumore: prima le date reali
(punto 1.8), poi il tuning.

**Fatto quando.** `docs/backtest.md` ha una sezione "v2" con delta
positivo; `/modello` è online; il test di regressione gira in CI.

---

### 6. Match Brief editoriale v2

**Obiettivo.** Dal "riassunto riformulato" al "programma di matchday": un
testo con sezioni, fatti ricchi, scritto una volta e servito in un istante.

**Cosa c'è già.** `BriefData`, template IT/EN, `OpenRouterClient` con
fallback garantito, hook "brief pronto entro 48h" in `ingest.py`.

**Linee guida.**

1. *Fatti più ricchi in ingresso.* Rank Elo dell'avversario e trend (punto
   3), precedenti con punteggi e date, giorni dall'ultima partita, striscia
   corrente, swing di momentum sulle ultime 5, split della community,
   casa/trasferta con stadio, orario. Tutto in `BriefData`, così il
   template resta la fonte di verità e l'LLM non può inventare.
2. *Output strutturato.* Chiedere sezioni fisse (Lo stato di forma,
   L'avversario, Il precedente, La chiave, Il verdetto del modello) come
   JSON via `response_format` se il modello lo supporta, altrimenti
   markdown con intestazioni fisse e parsing tollerante. Persona: "redattore
   del programma ufficiale della partita", tono sobrio, 120-180 parole,
   divieto esplicito di aggiungere fatti.
3. *Persistenza.* Tabella `briefs (match_id, kind, lang, model,
   sections_json, template_text, created_at)` con unique su
   `(match_id, kind, lang)`. Il brief pre viene generato dall'ingest quando
   la partita entra nella finestra 48h (stesso hook della notifica); il
   post subito dopo il ricalcolo a fine partita (punto 4.5). La pagina legge
   dal DB e non aspetta mai l'LLM; se manca, mostra il template e mette in
   coda la generazione.
4. *Post-partita onesto.* Sezione "Cosa ha detto il modello": esito più
   probabile vs reale, probabilità assegnata, delta Elo, e una riga
   sull'errore quando c'è stato.
5. *UI.* Layout a colonne da rivista, capolettera in oro, sezioni con
   titoletti in maiuscoletto, stemmi, il verdetto in una card separata con
   la barra delle probabilità.

**Insidie.** Cambio modello o prompt → invalidare la cache per `model`.
Costi: con la cache il numero di chiamate scende a due per partita.

**Fatto quando.** `/brief/next` risponde in meno di 500 ms con un brief a
sezioni; il DB contiene un brief per ogni partita giocata della stagione.

---

### 7. PWA installabile e notifiche ricche

**Obiettivo.** L'app sulla home del telefono di ogni amico, con notifiche
che sembrano di un'app vera.

**Cosa c'è già.** `sw.js`, `PushOptIn`, `push_sender.py` con tre eventi,
poller con rilevamento kickoff, resolver pronostici.

**Linee guida.**

1. *Manifest.* `app/manifest.ts` con `display: "standalone"`,
   `theme_color: "#000000"`, icone 192/512 anche `maskable`,
   `start_url: "/"`. Icone generate dallo stesso monogramma del punto 2.
2. *Legare la subscription al dispositivo.* `subscribeToPush` invia oggi
   `device_id: null`: passare il cookie, così le notifiche possono essere
   personali.
3. *Notifiche ricche.* Payload con `icon`, `badge`, `image` (stemma
   avversario o OG della partita), `actions` ("Pronostica", "Apri il
   brief") e `data.url`; `notificationclick` apre `data.url` invece di `/`.
4. *Nuovi eventi.* Gol: il poller confronta il punteggio precedente e
   invia "GOL · Juventus 1-0 Napoli". Fischio finale: risultato e delta
   Elo. Pronostico risolto: "Hai battuto il modello" o "Il modello ha
   visto giusto", per dispositivo. Tutti agganciati a transizioni già
   osservate dal poller.
5. *Dedup.* Colonna `momentum_notified_at` su `matches` (o tabella
   `notifications_sent (kind, key, sent_at)`) per chiudere il caso noto
   dello swing ri-notificato.

**Insidie.** iOS richiede l'installazione dalla home per il push: dirlo
nella UI. Non chiedere il permesso al primo caricamento: mostrare il
toggle solo dopo un'interazione o nella pagina della partita.

**Fatto quando.** Installata su iPhone e Android; una partita reale genera
kickoff, gol, fischio finale e risoluzione pronostico.

---

### 8. Pronostici v2: risultato esatto, classifica tra amici, card

**Obiettivo.** Il gioco tra amici che tiene viva l'app tutta la settimana,
senza account.

**Cosa c'è già.** `Prediction` con snapshot delle probabilità, resolver,
streak, statistiche community, `device_id`.

**Linee guida.**

1. *Modello dei gol.* Con 2.280 partite di lega si può stimare una
   regressione di Poisson `log(λ) = a + b * elo_diff` per casa e
   trasferta; opzionale la correzione Dixon-Coles sui risultati bassi.
   Matrice 0-6 × 0-6 → risultati più probabili e un 1/X/2 alternativo da
   confrontare nel backtest con l'euristica attuale: si tiene il migliore.
2. *Risultato esatto.* Stepper casa/trasferta accanto all'1/X/2; punteggio
   3 per esatto, 1 per esito; il modello gioca il suo risultato più
   probabile.
3. *Nickname.* Tabella `predictors (device_id, nickname, created_at)`;
   nickname scelto la prima volta, modificabile. Una classifica stagionale
   `/pronostici/classifica` per punti e per Brier score, con "vs modello".
   Pubblico ristretto: nessuna moderazione, nessun rate limit oltre
   l'unique già presente.
4. *Card condivisibile.* Route `app/pronostici/card/route.tsx` con
   `ImageResponse`: "Simone ha battuto il modello 7 volte su 10 · Juventum"
   in stile bianconero, per WhatsApp. Link "Condividi" con Web Share API.

**Insidie.** Il `device_id` cambia se si svuotano i cookie: offrire un
codice di recupero di 6 caratteri nel nickname, senza account.

**Fatto quando.** Tre amici in classifica dopo una giornata; una card
inviata su WhatsApp si vede con l'anteprima corretta.

---

### 9. La stagione in un colpo d'occhio

**Obiettivo.** La passione: una pagina che racconta la stagione con i
momenti calcolati dai dati.

**Cosa c'è già.** `juve_momentum` completa, `_compute_kpi`, `elo_ratings`
di entrambe le squadre (da cui la probabilità pre-partita di ogni gara
storica).

**Linee guida.**

1. *Endpoint.* `GET /momentum/highlights?season=`: picco e fondo del
   momentum, striscia più lunga, salto Elo massimo, sorpresa più grande
   (esito reale con la probabilità pre-partita più bassa), miglior/peggior
   partita per delta Elo, "la partita che ha cambiato la stagione" (massimo
   swing sulle 5 successive).
2. *UI.* Grafico annotato con `ReferenceDot` e didascalie, timeline
   verticale dei momenti con stemmi, confronto stagioni con overlay su asse
   "giornata" invece che data, card stagione condivisibile (stesso motore
   OG del punto 8).
3. *Sidebar.* Voce "Stagione" al posto di "Momentum Details", che diventa
   una sezione della stessa pagina.

**Fatto quando.** Ogni stagione con date reali ha almeno 5 momenti
annotati e il confronto multi-stagione funziona.

---

### 10. Velocità percepita, affidabilità, osservabilità

**Obiettivo.** Il "caro" si sente nella velocità e nel non rompersi mai
davanti a un amico.

**Linee guida.**

1. *Mai una pagina bianca.* `loading.tsx` per route con skeleton nella
   forma del contenuto; `error.tsx` con retry; `not-found.tsx` brandizzato.
   Suspense attorno ai blocchi lenti (brief, trasferte).
2. *Cache con invalidazione.* Sostituire `cache: "no-store"` con
   `next: { revalidate: 300, tags: ["matches"] }` per dati che cambiano al
   massimo ogni giornata; `no-store` solo per `/matches/live` e pronostici.
   Un route handler `POST /api/revalidate` con secret, chiamato dal backend
   alla fine dell'ingest e del fischio finale, che fa `revalidateTag`.
3. *Backend caldo.* Ping ogni 10 minuti a `/healthz` dal servizio cron
   scelto al punto 1.5; nei giorni di partita il poll-live lo tiene sveglio
   da solo.
4. *Polling intelligente.* `LiveMatchBanner` interroga `/matches/live`
   solo se il layout sa che oggi c'è una partita (`upcoming[0]` è oggi);
   altrimenti nessuna richiesta.
5. *Paginazione in SQL.* `GET /matches`: filtro `result` come espressione
   SQL (`case` su gol e squadra) e `offset/limit` nel DB.
6. *Osservabilità.* `@sentry/nextjs` e `sentry-sdk[fastapi]` (free tier),
   log JSON nel backend con `request_id`, `/healthz` con freschezza dati
   (punto 1.7), UptimeRobot sul frontend.
7. *Test frontend.* Vitest per formattazioni e i18n; Playwright con 3-4
   smoke (home, brief, partita, pronostico) contro `next start` e un
   backend con DB seminato in CI; Lighthouse CI con budget (Performance ≥
   90 mobile).
8. *Manutenzione.* Dependabot per npm e pip; preview deploy Vercel per
   ogni PR.

**Fatto quando.** Nessuna pagina bianca a freddo; Lighthouse mobile ≥ 90;
Sentry riceve un errore di prova; CI esegue almeno uno smoke e2e.

---

## Sequenza consigliata

1. **Settimana 0 — fondamenta.** Punto 1 completo, più i quick win sotto.
   Senza dati veri tutto il resto si vede su pagine vuote.
2. **Il salto visibile.** Punti 2 e 3 insieme: identità più classifica
   Elo è il massimo cambiamento percepito per effort speso, e la classifica
   dà al design contenuti veri su cui lavorare.
3. **Il sabato.** Punti 4, 6, 7: la partita come esperienza, prima durante
   e dopo, con il telefono in tasca.
4. **Profondità.** Punti 5, 8, 9 nell'ordine che si preferisce mostrare:
   rigore, gioco tra amici, racconto.
5. **In continuo.** Punto 10 spalmato dall'inizio: `loading.tsx`, cache e
   warm-up si fanno già nella settimana 0; Sentry e test e2e appena c'è il
   deploy.

## Quick win (meno di un'ora ciascuno)

- `--build` in `scripts/scheduled_ingest.sh` (o rimuovere il job locale
  quando arriva quello cloud).
- Valorizzare `ADMIN_TOKEN` in `backend/.env` e caricare il plist del live
  poll, se si vuole testare il live in locale prima del cloud.
- `app/icon.tsx` con il monogramma; `app/manifest.ts` minimo.
- `app/loading.tsx` radice con uno skeleton della shell.
- Brand "Juventum" in sidebar e `<title>`; riscrivere i quattro empty
  state e i badge del brief in `dictionaries.ts`.
- `subscribeToPush` con il `device_id` vero invece di `null`.
- `metadataBase` e `openGraph` in `layout.tsx`.
- Badge "date approssimate" sulle stagioni con `source='wikipedia'`.

## Linee guida trasversali

**Design.**
- Tre colori e basta: nero, bianco, oro. L'oro solo per ciò che conta
  (valore chiave, stato attivo, Juve nei grafici); verde/arancio/rosso solo
  per esiti V/N/P.
- Un numero protagonista per schermata. Il resto è di supporto.
- Ogni stato vuoto ha un perché e un'azione. Mai "nel dataset".
- Movimento come conferma, non come decorazione: 150-250 ms, easing
  standard, rispetto di `prefers-reduced-motion`.
- Mobile è il primo schermo, non l'ultimo.

**Ingegneria.**
- Ogni euristica resta dichiarata come oggi (`is_estimated`,
  `is_approximate`): la sincerità è parte del premium.
- Ogni cambiamento al modello passa dal backtest e lascia traccia in
  `docs/backtest.md`.
- Nessun nuovo servizio a pagamento; nessuna libreria UI; una sola font
  aggiunta.
- Le funzionalità nuove seguono i pattern esistenti: modulo puro in
  `features/`, endpoint sottile in `api/routes/`, schema Pydantic,
  migrazione Alembic, test per lo strato puro e per l'API.
- Verificare le API Next 16 nei docs in `node_modules` prima di scrivere
  codice frontend (regola in `frontend/AGENTS.md`).

**Cosa non fare.**
- Multi-club o white-label: diluisce l'identità che è il punto.
- Login e account: il `device_id` basta per un gruppo di amici.
- Logo o wordmark ufficiali Juventus.
- Feature che dipendono da API a pagamento (statistiche giocatori, xG,
  minuto live): fuori scope finché il free tier è un vincolo.

## Appendice — evidenze raccolte

Query sul Postgres locale (2026-09-09):

```
select count(*) from matches                      → 2280
… where home_team/away_team = 'Juventus FC'       → 228
select count(*) from juve_momentum                → 228
select min(match_date), max(match_date)           → 2019-08-15 … 2024-08-15
select season, count(*) group by season           → 2019-2020 … 2024-2025, 380 ciascuna
select source, count(*) group by source           → wikipedia 2280
select status, count(*) group by status           → FINISHED 2280
select count(*) from predictions                  → 0
select count(*) from push_subscriptions           → 0
partite Juve SCHEDULED/TIMED                      → nessuna
```

Estratto `logs/scheduled-ingest.log`:

```
=== Scheduled ingest run: Fri Sep  4 14:08:47 CEST 2026 ===
=== Done (exit 0): Fri Sep  4 14:09:45 CEST 2026 ===
=== Scheduled ingest run: Wed Sep  9 10:23:24 CEST 2026 ===
  File "/app/app/ingestion/ingest.py", line 43, in _ingest_competition_from_football_data
  File "/app/app/ingestion/football_data_client.py", line 93, in _get
    response.raise_for_status()
httpx.HTTPStatusError: Client error '403 ' for url '.../competitions/SA/matches?season=2022'
=== Done (exit 1): Wed Sep  9 10:23:38 CEST 2026 ===
```

Su `main` la stessa chiamata è alla riga 88 di `ingest.py` e il 403 è
intercettato alle righe 93-100 di `football_data_client.py`: l'immagine
Docker usata dal job è precedente a quella fix.

`launchctl list | grep juventum` → solo `com.juventum.scheduled-ingest`.

`frontend/public/` → solo `sw.js`. `frontend/app/` → nessun `loading.tsx`,
`error.tsx`, `not-found.tsx`, `manifest.ts`, `icon.tsx`.

Screenshot delle sei pagine (1440×1000, Brave headless): Overview con
"Prossime partite" vuota e tabelle con data ripetuta; Momentum Details con
asse X "15 ago 19 … 15 ago 24"; Matches con 228 righe tutte "15 ago 2024";
Match Brief senza avversario né probabilità; Trasferte e Pronostici in
empty state.
