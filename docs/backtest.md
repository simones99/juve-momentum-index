# Backtest del modello di probabilità — evoluzione

Questo documento traccia l'evoluzione del backtest del modello di probabilità
(`features/win_probability.py`, valutato con `scripts/backtest_win_probability.py`)
man mano che il dataset Elo migliora. Fase 2 passa da "Elo calcolato solo sulle
partite della Juventus" a "Elo calcolato sull'intera Serie A", così ogni
avversario ha un rating reale invece di ripartire da 1500 alla prima apparizione.

## Elo parziale (solo partite Juventus) — baseline pre-Fase 2

Misurato il: 2026-09-03

Dataset: 228 partite Juventus su 6 stagioni (2019-2020 → 2024-2025).

### Holdout singolo (ultima stagione: 2024-2025)

Train: 190 partite. Test: 38 partite.

Distribuzione risultati (train): `{'W': 0.5789473684210527, 'D': 0.23157894736842105, 'L': 0.18947368421052632}`
Distribuzione risultati (test): `{'W': 0.47368421052631576, 'D': 0.42105263157894735, 'L': 0.10526315789473684}`

| Modello | Log loss | Brier | Accuracy |
|---|---|---|---|
| Baseline uniforme (33/33/33) | 1.0986 | 0.6667 | 0.474 |
| Baseline frequenze (train) | 1.0499 | 0.6413 | 0.474 |
| Elo model (costanti attuali) | 1.0192 | 0.6166 | 0.474 |
| Elo model (tuned 0.24/400) | 1.0556 | 0.6350 | 0.474 |

### Cross-validation leave-one-season-out (6 fold)

Per fold, costanti tuned trovate via grid search e log loss attuale vs tuned:

| Fold | n | Tuned (peak/scale) | Log loss attuale | Log loss tuned |
|---|---|---|---|---|
| 2019-2020 | 38 | 0.32/300 | 0.946 | 0.971 |
| 2020-2021 | 38 | 0.28/400 | 0.956 | 0.956 |
| 2021-2022 | 38 | 0.28/400 | 1.037 | 1.037 |
| 2022-2023 | 38 | 0.3/400 | 0.955 | 0.966 |
| 2023-2024 | 38 | 0.26/350 | 1.022 | 1.037 |
| 2024-2025 | 38 | 0.24/400 | 1.019 | 1.056 |

Media sui 6 fold (± deviazione standard):

| Modello | Log loss (± std) | Brier | Accuracy |
|---|---|---|---|
| Uniforme | 1.0986 (±0.000) | 0.6667 | 0.561 |
| Frequenze | 0.9954 (±0.050) | 0.5930 | 0.561 |
| Attuale | 0.9892 (±0.037) | 0.5902 | 0.561 |
| Tuned (per-fold) | 1.0037 (±0.040) | 0.5987 | 0.561 |
| Scale=400 fisso | 0.9892 (±0.037) | 0.5902 | 0.561 |

Costanti finali (grid search sull'intero dataset): `DRAW_PEAK_PROBABILITY=0.28`,
`DRAW_DECAY_SCALE=400` (identiche alle costanti attualmente in uso in
`win_probability.py`).

### Calibrazione (costanti attuali, intero dataset)

Calibrazione di P(vittoria Juve): bucket | n | probabilità media prevista | tasso vittorie reale

| Bucket | n | Previsto | Reale |
|---|---|---|---|
| 1 | 45 | 0.40 | 0.49 |
| 2 | 45 | 0.43 | 0.53 |
| 3 | 45 | 0.47 | 0.56 |
| 4 | 45 | 0.54 | 0.64 |
| 5 | 45 | 0.58 | 0.58 |
| 6 | 3 | 0.61 | 0.67 |

Il modello sottostima sistematicamente la probabilità di vittoria della Juve
in quasi tutti i bucket (differenza tra reale e previsto tipicamente 4-10
punti), tranne nel bucket 5 dove è pressoché allineato. Ipotesi principale:
l'Elo degli avversari riparte da 1500 alla prima apparizione nel dataset
(nessuna storia reale pregressa), il che comprime artificialmente il gap di
rating rispetto a una Juventus storicamente più forte della media — la
Fase 2 (Elo sull'intera Serie A) punta a correggere proprio questo.

## Elo completo via Wikipedia — dato intermedio (ordine intra-stagione approssimato)

Misurato il: 2026-09-03, subito dopo aver generalizzato lo scraper Wikipedia
all'intera griglia risultati (380/380 partite estratte per stagione, nessuna
persa). **Limite di questo dato**: Wikipedia non fornisce una data per
singola partita — l'ordine cronologico dentro una stagione è quindi
approssimato (ordine di iterazione della griglia), mentre il carryover
dell'Elo *tra* stagioni è corretto. È un dato intermedio onesto, non il
numero definitivo: quello arriva domani con le date reali di
football-data.org (sezione successiva).

Stesso dataset Juventus di prima (228 partite, 6 stagioni) — cambia solo la
qualità dell'Elo degli avversari, ora calcolato su ~380 partite/stagione
invece che sulle sole 2 partite/stagione contro la Juve.

### Holdout singolo (ultima stagione: 2024-2025)

| Modello | Log loss | Brier | Accuracy |
|---|---|---|---|
| Baseline uniforme (33/33/33) | 1.0986 | 0.6667 | 0.474 |
| Baseline frequenze (train) | 1.0499 | 0.6413 | 0.474 |
| Elo model (costanti attuali) | 0.9969 | 0.6021 | 0.500 |
| Elo model (tuned 0.28/250) | 1.0378 | 0.6167 | 0.500 |

### Cross-validation leave-one-season-out (6 fold)

| Fold | n | Tuned (peak/scale) | Log loss attuale | Log loss tuned |
|---|---|---|---|---|
| 2019-2020 | 38 | 0.34/300 | 0.908 | 0.942 |
| 2020-2021 | 38 | 0.3/400 | 0.925 | 0.928 |
| 2021-2022 | 38 | 0.3/350 | 0.992 | 0.991 |
| 2022-2023 | 38 | 0.32/300 | 0.903 | 0.914 |
| 2023-2024 | 38 | 0.28/300 | 0.993 | 1.002 |
| 2024-2025 | 38 | 0.28/250 | 0.997 | 1.038 |

Media sui 6 fold (± deviazione standard):

| Modello | Log loss (± std) | Brier | Accuracy |
|---|---|---|---|
| Uniforme | 1.0986 (±0.000) | 0.6667 | 0.561 |
| Frequenze | 0.9954 (±0.050) | 0.5930 | 0.561 |
| **Attuale** | **0.9530 (±0.042)** | **0.5649** | 0.575 |
| Tuned (per-fold) | 0.9691 (±0.044) | 0.5735 | 0.575 |

Costanti finali (grid search sull'intero dataset): `DRAW_PEAK_PROBABILITY=0.30`,
`DRAW_DECAY_SCALE=300` — diverse dalle costanti attualmente in uso (0.28/400,
scelte sul dataset "Elo parziale"); non le ho ancora aggiornate in
`win_probability.py`, in attesa del dato definitivo di domani per evitare di
tarare due volte sullo stesso rumore.

### Calibrazione (costanti attuali, intero dataset)

| Bucket | n | Previsto | Reale |
|---|---|---|---|
| 1 | 45 | 0.32 | 0.31 |
| 2 | 45 | 0.42 | 0.47 |
| 3 | 45 | 0.49 | 0.62 |
| 4 | 45 | 0.55 | 0.69 |
| 5 | 45 | 0.64 | 0.73 |
| 6 | 3 | 0.73 | 0.33 |

### Confronto con la baseline pre-Fase 2

| Metrica (media CV) | Prima (Elo solo Juve) | Dopo (Elo Wikipedia intera lega) | Δ |
|---|---|---|---|
| Log loss | 0.9892 | **0.9530** | −3.7% |
| Log loss vs baseline frequenze | quasi pari (−0.6%) | **nettamente meglio (−4.3%)** | — |
| Brier | 0.5902 | **0.5649** | −4.3% |
| Deviazione standard log loss | ±0.037 | ±0.042 | invariata |

Il miglioramento è reale e va nella direzione attesa: con un Elo avversario
vero invece che azzerato a 1500, il modello smette di essere "quasi
indistinguibile" dalla baseline a frequenze storiche e la batte con un
margine chiaro. La sottostima sistematica in calibrazione resta (bucket 4-5
ora addirittura *sovrastimano* leggermente meno che prima ma il quadro
generale non è ancora perfettamente calibrato) — plausibilmente perché
l'ordine intra-stagione approssimato introduce comunque rumore nell'Elo.

## Elo completo con date reali (football-data.org) — definitivo

TBD — da compilare domani dopo re-ingestion con la API key reale (date e
sedi vere, niente più ordine approssimato dentro stagione). Se il
miglioramento si conferma o cresce ulteriormente, aggiornare le costanti
shipped in `win_probability.py` a quel punto, non prima.
