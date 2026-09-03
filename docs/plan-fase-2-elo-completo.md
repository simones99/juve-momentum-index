# Fase 2 — Elo completo su tutta la Serie A + nuovo backtest

Stato (2026-09-03): **step 1-5 implementati per la parte eseguibile senza API key**
(identità squadre, client football-data.org per competizione + regola
anti-duplicati, scraper Wikipedia a griglia intera, ordinamento deterministico,
backtest congelato e ri-misurato — vedi `docs/backtest.md`). Verificato anche
con un re-ingest reale: 380/380 partite estratte per stagione, miglioramento
del backtest confermato (log loss CV 0.989 → 0.953). Resta da fare domani con
la API key: verifica reale del client football-data.org (mai testato contro
l'API vera), completamento della mappa alias con `scripts/check_team_names.py`,
backtest definitivo con date reali, decisione sul tuning K/home-advantage
(step 4 del piano sotto).

## Obiettivo

Oggi il dataset contiene solo le 38 partite/stagione della Juventus. Ogni
avversario "riparte da 1500" alla prima apparizione e il suo Elo evolve solo
attraverso le partite contro la Juve — è il limite #1 documentato in `elo.py` e
nel README, e quasi certamente la causa principale della sottostima sistematica
(7-10 punti) emersa nella calibrazione del backtest.

Risultato atteso: ingerire **tutte** le partite della lega (380/stagione di
Serie A, più tutta la Champions quando disponibile), così l'Elo di ogni
avversario è reale, e **misurare** il miglioramento ri-eseguendo lo stesso
backtest (`scripts/backtest_win_probability.py`) prima/dopo. Storia da CV:
limite identificato → risolto → quantificato.

Nessuna modifica allo schema DB. Nessuna modifica al frontend.

## Cosa già funziona (verificato nel codice)

- `features/recompute.py::recompute_all_derived` carica **tutte** le partite in
  ordine cronologico, calcola l'Elo di entrambe le squadre di ogni partita e
  scrive `elo_ratings` per tutte; `juve_momentum` resta filtrata sulla Juve.
  → Con la lega intera, l'Elo avversario diventa reale senza toccare il calcolo.
- Tutti gli endpoint (`/matches`, `/seasons`, `/competitions`, `/momentum/*`,
  `/brief/*`, `/matches/upcoming`, `/travel/*`) filtrano già su `TEAM_NAME`.
  → Le partite non-Juve nel DB non "sporcano" la UI.
- `briefs/template_brief.py::_current_elo(db, team)` legge `elo_ratings` →
  userà automaticamente il rating reale dell'avversario.
- `scripts/backtest_win_probability.py` legge `juve_momentum` + `elo_ratings`
  → si ri-esegue tale e quale, il confronto è pulito.

## Piano in 5 step

### 1. Identità delle squadre tra fonti diverse (prerequisito, rischio #1)

Problema: con la lega intera, ogni club compare in centinaia di righe e da due
fonti. Wikipedia usa il `title` dei link ("Atalanta BC"), football-data.org i
propri nomi ufficiali ("FC Internazionale Milano" vs il "Inter Milan" di
Wikipedia). Un solo mismatch spezza in due la storia Elo di quel club — lo
stesso bug già visto con "A.C. Milan"/"AC Milan", ma su scala 20×.

- Nuovo `app/core/teams.py`: nome canonico + alias per ogni club, unico posto
  dove vive l'identità. `canonicalize_team_name()` in `normalize.py` passa da
  "solo Juventus + strip dei punti" a lookup nella mappa alias (mantenendo lo
  strip dei punti come pre-normalizzazione).
- `app/core/stadiums.py` si ri-chiava sui nomi canonici (oggi coincide con i
  nomi Wikipedia già normalizzati; verificare che restino allineati).
- Nuovo `scripts/check_team_names.py`: dopo un'ingestion stampa i nomi distinti
  per fonte e segnala quelli **non** mappati — è il modo per scoprire gli alias
  dell'API il giorno in cui arriva la key, invece di indovinarli ora.
- Test: `tests/test_normalize.py` esteso agli alias multi-club (Inter, Milan,
  Roma, Lazio, Napoli, Fiorentina...).

### 2. Ingestion di tutta la lega

Due sorgenti, stessa interfaccia (`list[MatchIn]` per stagione/competizione):

**A. Wikipedia (fattibile oggi, senza key).** `wikipedia_scraper.py`: la griglia
risultati che già scarichiamo contiene *tutte* le 380 partite (riga=casa,
colonna=trasferta). Oggi estraiamo solo riga e colonna Juve; estrarre l'intera
matrice è una generalizzazione dello stesso loop. Limiti dichiarati:
- **Nessuna data per partita** (placeholder unico a inizio stagione). L'Elo è
  sensibile all'ordine: dentro una stagione l'ordine sarà quello di
  iterazione della griglia, non cronologico. Il carryover *tra* stagioni è
  invece corretto. Va scritto nel README come approssimazione temporanea.
- Celle con annotazioni (partite assegnate a tavolino, es. "0–3 (a)") non
  matchano `SCORE_PATTERN` → loggare il conteggio per stagione e avvisare se
  < 380, non fallire in silenzio.
- Solo Serie A (nessuna Champions).

**B. football-data.org (quando c'è la key).** Nuovo metodo
`FootballDataClient.get_competition_matches(code, season)` →
`GET /competitions/{SA|CL}/matches?season=YYYY`: tutte le partite della
competizione, **con date/orari reali, sedi e fixture future**. Include anche
le partite CL tra squadre non italiane (danno un Elo anche a loro: innocuo).
- Rate limit 10 req/min: 6 stagioni × 2 competizioni = 12 chiamate, il
  throttle esistente (6.5 s) le gestisce in ~80 s.
- Rischio da verificare col primo test reale: il free tier potrebbe limitare
  le stagioni storiche. Se sì, il disegno naturale è **ibrido**: API per
  stagione corrente e future (date, sedi, calendario), Wikipedia per lo
  storico profondo.
- `JUVENTUS_TEAM_ID` non serve più (l'endpoint per competizione non richiede
  il team id, e include anche le partite future della Juve per "Prossime
  partite"/"Trasferte"). Rimuoverlo da `config.py`, `.env.example`,
  `docker-compose.yml`, README; `scripts/resolve_team_id.py` diventa
  superfluo.

**Regola anti-duplicati (gotcha reale).** L'upsert usa la chiave naturale
`(season, competition, home, away, match_date)`: le righe Wikipedia (data
placeholder) e API (data reale) della *stessa* partita non collidono → si
duplicherebbero. `update_matches` deve trattare la stagione come
**mono-sorgente**: quando l'API ha successo per una stagione, cancellare prima
le righe `source='wikipedia'` di quella stagione, poi inserire. Test dedicato.

**Ordinamento deterministico.** `recompute.py` ordina per
`(match_date, id)` invece del solo `match_date`, così a parità di data
(Wikipedia) il risultato è riproducibile tra esecuzioni.

### 3. Ri-esecuzione del backtest e misura (il cuore della fase)

- Prima di toccare i dati, congelare i numeri attuali in `docs/backtest.md`
  (sezione "Elo parziale, solo partite Juve"): CV log loss 0.989 vs baseline
  frequenze 0.995, Brier 0.590, accuracy 0.561, tabella di calibrazione con
  sottostima 7-10 punti.
- Re-ingest completo (truncate + `ingest` con la lega intera) →
  `recompute_all_derived` → `scripts/backtest_win_probability.py`.
- Aggiungere a `docs/backtest.md` la sezione "Elo completo" con gli stessi
  indicatori e il delta. Esito onesto qualunque sia: se il miglioramento è
  piccolo o nullo, resta un risultato da riportare (e sposta il sospetto su
  K-factor/home advantage, vedi step 4).
- Attenzione al confronto: con la sola via Wikipedia (ordine intra-stagione
  approssimato) il delta è indicativo; il numero "buono" è quello con le date
  reali dell'API.

### 4. (Opzionale, decidere dopo lo step 3) Tuning di K_FACTOR e HOME_ADVANTAGE

Con l'Elo reale ha finalmente senso ottimizzare i parametri dell'Elo stesso,
non solo quelli del modello di pareggio. `compute_elo_history` è pura: il
backtest può ricalcolare l'intera storia Elo per ogni candidato (K ∈ {10…40},
home advantage ∈ {40…100}) e valutarlo con la stessa leave-one-season-out CV.
**Trade-off da esplicitare:** K e home advantage alimentano anche il Momentum
Index — cambiarli cambia i grafici di tutta l'app, non solo le probabilità.
Farlo solo se lo step 3 mostra che il collo di bottiglia è lì, e documentarlo.

### 5. Documentazione

- README: il limite "Elo semplificato" diventa "Elo completo su Serie A
  (Wikipedia/API); Champions solo via API"; sezione backtest aggiornata con
  prima/dopo; setup senza `JUVENTUS_TEAM_ID`.
- Docstring di `elo.py`: rimuovere/aggiornare la nota sul dataset parziale.

## Test da aggiungere/aggiornare

- `tests/test_wikipedia_scraper.py` (nuovo): griglia HTML sintetica di 4
  squadre offline → 12 partite estratte, celle annotate ignorate con warning,
  nomi risolti via `<a title>`.
- `tests/test_recompute.py` (nuovo): con una partita non-Juve nel DB,
  `elo_ratings` la include, `juve_momentum` no; ordinamento `(match_date, id)`
  riproducibile.
- `tests/test_ingest.py` (nuovo): regola mono-sorgente per stagione (le righe
  Wikipedia vengono sostituite quando l'API riesce); client API mockato.
- `tests/test_normalize.py`: alias multi-club.
- Suite esistente (52 test) deve restare verde senza modifiche di
  comportamento visibili.

## Verifica end-to-end

1. `pytest -q` verde.
2. Ingestion Wikipedia lega intera su 6 stagioni: attesi ~2.280 match
   (380×6), `scripts/check_team_names.py` senza nomi non mappati, 20 squadre
   per stagione in `elo_ratings`.
3. Backtest prima/dopo in `docs/backtest.md`.
4. Con la key: `check_team_names.py` sull'output API → completare la mappa
   alias → re-ingest → backtest "definitivo" con date reali; verificare che
   "Prossime partite" e "Trasferte" si popolino senza `JUVENTUS_TEAM_ID`.
5. `/matches`, `/seasons`, `/momentum/overview` via curl: solo Juve, invariati.

## Effort stimato

Step 1-2: la parte grossa (nuovo modulo identità, scraper generalizzato,
endpoint API, regola anti-duplicati, 3 file di test). Step 3: veloce, è
esecuzione + scrittura. Step 4: da decidere. Step 5: piccolo.

## Rischi

| Rischio | Mitigazione |
|---|---|
| Alias API sconosciuti finché non c'è la key | `check_team_names.py` li rende visibili; nessuna ipotesi hardcoded |
| Free tier senza stagioni storiche | Design ibrido API+Wikipedia già previsto |
| Ordine intra-stagione approssimato (Wikipedia) | Dichiarato; superato dalle date API |
| Celle annotate nella griglia | Conteggio per stagione + warning |
| Duplicati tra fonti | Stagione mono-sorgente + test |
| Step 4 cambia il Momentum Index | Opzionale, documentato, deciso dopo i numeri |
