# Probability model backtest — history

This document tracks the backtest of the probability model
(`features/win_probability.py`, evaluated with `scripts/backtest_win_probability.py`)
as the Elo dataset improves. Phase 2 moves from "Elo computed on Juventus
matches only" to "Elo computed on the whole Serie A", so that every opponent
has a real rating instead of restarting from 1500 on its first appearance.

## Partial Elo (Juventus matches only) — pre-Phase 2 baseline

Measured on: 2026-09-03

Dataset: 228 Juventus matches over 6 seasons (2019-2020 → 2024-2025).

### Single holdout (last season: 2024-2025)

Train: 190 matches. Test: 38 matches.

Outcome distribution (train): `{'W': 0.5789473684210527, 'D': 0.23157894736842105, 'L': 0.18947368421052632}`
Outcome distribution (test): `{'W': 0.47368421052631576, 'D': 0.42105263157894735, 'L': 0.10526315789473684}`

| Model | Log loss | Brier | Accuracy |
|---|---|---|---|
| Uniform baseline (33/33/33) | 1.0986 | 0.6667 | 0.474 |
| Frequency baseline (train) | 1.0499 | 0.6413 | 0.474 |
| Elo model (current constants) | 1.0192 | 0.6166 | 0.474 |
| Elo model (tuned 0.24/400) | 1.0556 | 0.6350 | 0.474 |

### Leave-one-season-out cross-validation (6 folds)

For each fold: constants tuned by grid search, and log loss with the current vs the tuned constants:

| Fold | n | Tuned (peak/scale) | Log loss, current | Log loss, tuned |
|---|---|---|---|---|
| 2019-2020 | 38 | 0.32/300 | 0.946 | 0.971 |
| 2020-2021 | 38 | 0.28/400 | 0.956 | 0.956 |
| 2021-2022 | 38 | 0.28/400 | 1.037 | 1.037 |
| 2022-2023 | 38 | 0.3/400 | 0.955 | 0.966 |
| 2023-2024 | 38 | 0.26/350 | 1.022 | 1.037 |
| 2024-2025 | 38 | 0.24/400 | 1.019 | 1.056 |

Mean over the 6 folds (± standard deviation):

| Model | Log loss (± std) | Brier | Accuracy |
|---|---|---|---|
| Uniform | 1.0986 (±0.000) | 0.6667 | 0.561 |
| Frequency | 0.9954 (±0.050) | 0.5930 | 0.561 |
| Current | 0.9892 (±0.037) | 0.5902 | 0.561 |
| Tuned (per fold) | 1.0037 (±0.040) | 0.5987 | 0.561 |
| Fixed scale=400 | 0.9892 (±0.037) | 0.5902 | 0.561 |

Final constants (grid search on the full dataset): `DRAW_PEAK_PROBABILITY=0.28`,
`DRAW_DECAY_SCALE=400` (the same as the constants currently used in
`win_probability.py`).

### Calibration (current constants, full dataset)

Calibration of P(Juventus win): bucket | n | mean predicted probability | actual win rate

| Bucket | n | Predicted | Actual |
|---|---|---|---|
| 1 | 45 | 0.40 | 0.49 |
| 2 | 45 | 0.43 | 0.53 |
| 3 | 45 | 0.47 | 0.56 |
| 4 | 45 | 0.54 | 0.64 |
| 5 | 45 | 0.58 | 0.58 |
| 6 | 3 | 0.61 | 0.67 |

The model systematically underestimates Juventus's win probability in almost
every bucket (actual minus predicted is typically 4–10 points), except bucket 5,
where it is roughly aligned. Main hypothesis: opponents' Elo restarts from 1500
on their first appearance in the dataset (no real past history), which
artificially compresses the rating gap to a Juventus that has historically been
stronger than average. Phase 2 (Elo on the whole Serie A) aims to fix exactly
this.

## Full Elo from Wikipedia — interim result (approximate within-season order)

Measured on: 2026-09-03, right after generalising the Wikipedia scraper to the
full results grid (380/380 matches extracted per season, none lost).
**Limitation of this result**: Wikipedia gives no date for individual matches,
so the chronological order within a season is approximate (the iteration order
of the grid), while the Elo carry-over *between* seasons is correct. This is an
honest interim figure, not the final one: that came with the real dates from
football-data.org (next section).

Same Juventus dataset as before (228 matches, 6 seasons). Only the quality of
the opponents' Elo changes: it is now computed on ~380 matches per season
instead of the 2 matches per season played against Juventus.

### Single holdout (last season: 2024-2025)

| Model | Log loss | Brier | Accuracy |
|---|---|---|---|
| Uniform baseline (33/33/33) | 1.0986 | 0.6667 | 0.474 |
| Frequency baseline (train) | 1.0499 | 0.6413 | 0.474 |
| Elo model (current constants) | 0.9969 | 0.6021 | 0.500 |
| Elo model (tuned 0.28/250) | 1.0378 | 0.6167 | 0.500 |

### Leave-one-season-out cross-validation (6 folds)

| Fold | n | Tuned (peak/scale) | Log loss, current | Log loss, tuned |
|---|---|---|---|---|
| 2019-2020 | 38 | 0.34/300 | 0.908 | 0.942 |
| 2020-2021 | 38 | 0.3/400 | 0.925 | 0.928 |
| 2021-2022 | 38 | 0.3/350 | 0.992 | 0.991 |
| 2022-2023 | 38 | 0.32/300 | 0.903 | 0.914 |
| 2023-2024 | 38 | 0.28/300 | 0.993 | 1.002 |
| 2024-2025 | 38 | 0.28/250 | 0.997 | 1.038 |

Mean over the 6 folds (± standard deviation):

| Model | Log loss (± std) | Brier | Accuracy |
|---|---|---|---|
| Uniform | 1.0986 (±0.000) | 0.6667 | 0.561 |
| Frequency | 0.9954 (±0.050) | 0.5930 | 0.561 |
| **Current** | **0.9530 (±0.042)** | **0.5649** | 0.575 |
| Tuned (per fold) | 0.9691 (±0.044) | 0.5735 | 0.575 |

Final constants (grid search on the full dataset): `DRAW_PEAK_PROBABILITY=0.30`,
`DRAW_DECAY_SCALE=300`. These differ from the constants currently in use
(0.28/400, chosen on the "partial Elo" dataset). They were not applied to
`win_probability.py` yet, pending the final dataset, to avoid tuning twice on
the same noise.

### Calibration (current constants, full dataset)

| Bucket | n | Predicted | Actual |
|---|---|---|---|
| 1 | 45 | 0.32 | 0.31 |
| 2 | 45 | 0.42 | 0.47 |
| 3 | 45 | 0.49 | 0.62 |
| 4 | 45 | 0.55 | 0.69 |
| 5 | 45 | 0.64 | 0.73 |
| 6 | 3 | 0.73 | 0.33 |

### Comparison with the pre-Phase 2 baseline

| Metric (CV mean) | Before (Juventus-only Elo) | After (whole-league Elo from Wikipedia) | Δ |
|---|---|---|---|
| Log loss | 0.9892 | **0.9530** | −3.7% |
| Log loss vs frequency baseline | almost equal (−0.6%) | **clearly better (−4.3%)** | — |
| Brier | 0.5902 | **0.5649** | −4.3% |
| Log loss standard deviation | ±0.037 | ±0.042 | similar |

The improvement is real and goes in the expected direction: with real opponent
Elo instead of a reset to 1500, the model stops being almost indistinguishable
from the historical-frequency baseline and beats it by a clear margin.
Calibration is still not good. The lowest bucket is now well calibrated, but
the model still underestimates the win probability in buckets 2–5, and in
buckets 3–5 the gap is larger than before (11–14 points). A plausible cause is
the noise that the approximate within-season order adds to the Elo.

## Full Elo with real dates (football-data.org) — final

Measured on: 2026-09-15, after the first real ingest with the football-data.org
key. The free tier only covers a rolling window of seasons: 2023-2024 →
2026-2027 come from football-data.org with real dates and venues; 2019-2020 →
2022-2023 returned 403 and stayed on the Wikipedia fallback (placeholder date
at the start of the season, marked in the UI by an "approximate date" badge).

Dataset: 290 Juventus matches over 8 seasons (2019-2020 → 2026-2027), 62 more
than in the previous section, because the 2025-2026 and 2026-2027 seasons were
ingested in the meantime (the latter is in progress, with only 4 matches
played so far).

### Single holdout (last season: 2026-2027)

Train: 286 matches. Test: 4 matches (season in progress, minimal sample).

Outcome distribution (train): `{'W': 0.542, 'D': 0.276, 'L': 0.182}`
Outcome distribution (test): `{'W': 0.5, 'D': 0.25, 'L': 0.25}`

| Model | Log loss | Brier | Accuracy |
|---|---|---|---|
| Uniform baseline (33/33/33) | 1.0986 | 0.6667 | 0.500 |
| Frequency baseline (train) | 1.0541 | 0.6321 | 0.500 |
| Elo model (current constants) | 0.9559 | 0.5628 | 0.500 |
| Elo model (tuned 0.3/400) | 0.9574 | 0.5640 | 0.500 |

### Leave-one-season-out cross-validation (8 folds)

| Fold | n | Tuned (peak/scale) | Log loss, current | Log loss, tuned |
|---|---|---|---|---|
| 2019-2020 | 38 | 0.32/400 | 0.908 | 0.937 |
| 2020-2021 | 38 | 0.3/400 | 0.925 | 0.928 |
| 2021-2022 | 38 | 0.3/400 | 0.992 | 0.993 |
| 2022-2023 | 38 | 0.32/400 | 0.903 | 0.924 |
| 2023-2024 | 38 | 0.28/400 | 0.998 | 0.998 |
| 2024-2025 | 48 | 0.28/400 | 1.034 | 1.034 |
| 2025-2026 | 48 | 0.28/400 | 1.003 | 1.003 |
| 2026-2027 | 4 | 0.3/400 | 0.956 | 0.957 |

Mean over the 8 folds (± standard deviation):

| Model | Log loss (± std) | Brier | Accuracy |
|---|---|---|---|
| Uniform | 1.0986 (±0.000) | 0.6667 | 0.542 |
| Frequency | 1.0096 (±0.047) | 0.6040 | 0.542 |
| **Current** | **0.9649 (±0.046)** | **0.5733** | 0.550 |
| Tuned (per fold) | 0.9717 (±0.038) | 0.5784 | 0.550 |

Final constants (grid search on the full dataset): `DRAW_PEAK_PROBABILITY=0.3`,
`DRAW_DECAY_SCALE=400`. In cross-validation, however, the **current** constants
(0.28/400) remain better (mean log loss 0.9649 vs 0.9717): the grid search on
the full dataset overfits again, the same pattern seen in the previous section.
**Constants not updated**: `win_probability.py` stays at 0.28/400, as the
decision rule requires. Constants are changed only if the tuned ones beat the
current ones in cross-validation, which is not the case here.

Caveat: the current constants were themselves chosen on the "partial Elo"
dataset, whose seasons overlap these folds. The per-fold tuned figure (0.9717)
is therefore the cleaner out-of-sample estimate.

### Calibration (current constants, full dataset)

| Bucket | n | Predicted | Actual |
|---|---|---|---|
| 1 | 58 | 0.31 | 0.29 |
| 2 | 58 | 0.44 | 0.47 |
| 3 | 58 | 0.49 | 0.60 |
| 4 | 58 | 0.56 | 0.67 |
| 5 | 58 | 0.65 | 0.67 |

### Comparison with the previous section (whole-league Elo from Wikipedia)

| Metric (CV mean) | Before (Wikipedia, 6 seasons / 228 matches) | After (real dates, 8 seasons / 290 matches) | Δ |
|---|---|---|---|
| Log loss | 0.9530 | 0.9649 | +1.2% (worse) |
| Brier | 0.5649 | 0.5733 | +1.5% (worse) |

Mean log loss is slightly worse than in the previous section, but the datasets
differ, so the comparison is not like for like:
- two seasons were added: 2025-2026 complete, and 2026-2027 with only 4 matches,
  the fold with the highest variance;
- 2024-2025 now has 48 matches instead of 38.

On the six seasons in common (2019-2020 → 2024-2025), the four seasons that are
still on Wikipedia dates have identical per-fold log loss. The two seasons that
received real dates are slightly worse: 2023-2024 goes from 0.993 to 0.998, and
2024-2025 from 0.997 to 1.034, the latter with a different set of matches.
These numbers do not show a benefit from real dates yet.

Calibration is in the same picture as the previous section: systematic
underestimation in the middle and upper buckets, unchanged by the switch to real
dates. This points to the probability model itself (draw-peak heuristic, no
margin of victory, no seasonal regression) rather than to the quality of the
match dates.

**Next step for a clean comparison**: re-run this backtest once the 2026-2027
season is complete, so that the last fold has normal variance instead of 4
matches.
