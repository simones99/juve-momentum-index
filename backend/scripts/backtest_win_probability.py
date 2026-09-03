"""Backtests the Elo-based win/draw/loss probability model (see
app/features/win_probability.py) against real historical results, and
scores it the way a probabilistic ML classifier would be scored:
multi-class log loss, Brier score, accuracy, and a calibration check —
each against two baselines (uniform, and the training set's empirical
class frequencies).

Methodology (chronological train/test split, no leakage):
  - TRAIN: all seasons except the most recent one.
  - TEST:  the most recent season only, held out entirely.
  - Hyperparameters (DRAW_PEAK_PROBABILITY, DRAW_DECAY_SCALE) are grid-
    searched to minimize log loss ON THE TRAIN SET ONLY, then both the
    shipped defaults and the tuned values are scored on the untouched
    TEST set. Only a genuine test-set improvement is reported as such.

Usage (from backend/, with the DB populated for >= 2 seasons):
    python scripts/backtest_win_probability.py
"""

import math
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.features.elo import HOME_ADVANTAGE, expected_score  # noqa: E402
from app.features.win_probability import DRAW_DECAY_SCALE, DRAW_PEAK_PROBABILITY  # noqa: E402
from app.models.elo_rating import EloRating  # noqa: E402
from app.models.juve_momentum import JuveMomentum  # noqa: E402

OUTCOMES = ("W", "D", "L")


@dataclass(frozen=True)
class Sample:
    season: str
    match_date: object
    opponent: str
    is_home: bool
    juve_elo_before: float
    opponent_elo_before: float
    result: str  # "W" | "D" | "L"


def _opponent_elo_before(db: Session, match_id: int, opponent: str) -> float | None:
    rating = db.scalar(
        select(EloRating.elo_before).where(EloRating.match_id == match_id, EloRating.team == opponent)
    )
    return float(rating) if rating is not None else None


def load_samples(db: Session) -> list[Sample]:
    rows = list(db.scalars(select(JuveMomentum).order_by(JuveMomentum.match_date.asc())))
    samples = []
    skipped = 0
    for row in rows:
        opponent_elo = _opponent_elo_before(db, row.match_id, row.opponent)
        if opponent_elo is None:
            skipped += 1
            continue
        samples.append(
            Sample(
                season=row.season,
                match_date=row.match_date,
                opponent=row.opponent,
                is_home=row.home_away == "H",
                juve_elo_before=float(row.elo_before),
                opponent_elo_before=opponent_elo,
                result=row.result,
            )
        )
    if skipped:
        print(f"(skipped {skipped} match(es) with no opponent Elo record)")
    return samples


def _match_probabilities(rating_home: float, rating_away: float, draw_peak: float, draw_scale: float) -> dict[str, float]:
    """Same math as features/win_probability.py's estimate_match_probabilities(),
    but with draw_peak/draw_scale passed explicitly so the grid search below
    can vary them per call (the real function's `scale` default is bound at
    import time, so patching the module constant would silently no-op)."""
    adjusted_home = rating_home + HOME_ADVANTAGE
    home_win_share = expected_score(adjusted_home, rating_away)
    draw = draw_peak * math.exp(-0.5 * ((adjusted_home - rating_away) / draw_scale) ** 2)
    return {
        "home": home_win_share * (1 - draw),
        "draw": draw,
        "away": (1 - home_win_share) * (1 - draw),
    }


def predict(sample: Sample, draw_peak: float, draw_scale: float) -> dict[str, float]:
    if sample.is_home:
        probs = _match_probabilities(sample.juve_elo_before, sample.opponent_elo_before, draw_peak, draw_scale)
        return {"W": probs["home"], "D": probs["draw"], "L": probs["away"]}
    probs = _match_probabilities(sample.opponent_elo_before, sample.juve_elo_before, draw_peak, draw_scale)
    return {"W": probs["away"], "D": probs["draw"], "L": probs["home"]}


def log_loss(samples: list[Sample], predictions: list[dict[str, float]], eps: float = 1e-9) -> float:
    total = 0.0
    for sample, probs in zip(samples, predictions):
        p = max(probs[sample.result], eps)
        total += -math.log(p)
    return total / len(samples)


def brier_score(samples: list[Sample], predictions: list[dict[str, float]]) -> float:
    total = 0.0
    for sample, probs in zip(samples, predictions):
        total += sum((probs[o] - (1.0 if o == sample.result else 0.0)) ** 2 for o in OUTCOMES)
    return total / len(samples)


def accuracy(samples: list[Sample], predictions: list[dict[str, float]]) -> float:
    correct = sum(
        1 for sample, probs in zip(samples, predictions) if max(probs, key=probs.get) == sample.result
    )
    return correct / len(samples)


def class_frequencies(samples: list[Sample]) -> dict[str, float]:
    counts = Counter(s.result for s in samples)
    n = len(samples)
    return {o: counts.get(o, 0) / n for o in OUTCOMES}


def score_model(name: str, samples: list[Sample], predictions: list[dict[str, float]]) -> None:
    print(
        f"  {name:<28} log loss = {log_loss(samples, predictions):.4f}   "
        f"brier = {brier_score(samples, predictions):.4f}   "
        f"accuracy = {accuracy(samples, predictions):.3f}"
    )


def calibration_table(samples: list[Sample], predictions: list[dict[str, float]], n_buckets: int = 5) -> None:
    """Buckets predicted P(Juve win) into quantile-ish bins and compares the
    mean predicted probability to the actual Juve win rate in each bucket —
    a well-calibrated model has the two columns close together."""
    paired = sorted(zip(predictions, samples), key=lambda ps: ps[0]["W"])
    bucket_size = max(1, len(paired) // n_buckets)
    print("  Calibrazione P(vittoria Juve): bucket | n | prob. media prevista | tasso vittorie reale")
    for i in range(0, len(paired), bucket_size):
        chunk = paired[i : i + bucket_size]
        if not chunk:
            continue
        mean_pred = sum(p["W"] for p, _ in chunk) / len(chunk)
        actual_rate = sum(1 for _, s in chunk if s.result == "W") / len(chunk)
        print(f"    [{i // bucket_size + 1}] n={len(chunk):<3} previsto={mean_pred:.2f}   reale={actual_rate:.2f}")


def grid_search(train: list[Sample]) -> tuple[float, float]:
    draw_peaks = [0.20, 0.22, 0.24, 0.26, 0.28, 0.30, 0.32, 0.34]
    draw_scales = [100.0, 150.0, 200.0, 250.0, 300.0, 350.0, 400.0]
    best = (DRAW_PEAK_PROBABILITY, DRAW_DECAY_SCALE)
    best_loss = float("inf")
    for peak in draw_peaks:
        for scale in draw_scales:
            preds = [predict(s, peak, scale) for s in train]
            loss = log_loss(train, preds)
            if loss < best_loss:
                best_loss = loss
                best = (peak, scale)
    return best


def leave_one_season_out_cv(samples: list[Sample], seasons: list[str]) -> None:
    """The single-season holdout above is noisy — 38 matches/season is a
    small, high-variance sample (see how different the train/test class
    distributions turned out above). Leave-one-season-out CV scores every
    season as a held-out fold and averages the result, which is far less
    sensitive to any one season being unusual. Per fold, hyperparameters are
    re-tuned on the other 5 seasons only (nested — never touching the held-
    out fold), so the "tuned" numbers are an honest out-of-sample estimate,
    not a fitted-and-graded-on-the-same-data number.
    """
    print(f"\n{'=' * 70}\nLeave-one-season-out cross-validation ({len(seasons)} fold)\n{'=' * 70}")

    variant_names = ("uniforme", "frequenze", "attuale", "tuned", "scale=400 fisso")
    fold_losses = {name: [] for name in variant_names}
    fold_briers = {name: [] for name in variant_names}
    fold_accs = {name: [] for name in variant_names}

    for held_out in seasons:
        train_fold = [s for s in samples if s.season != held_out]
        test_fold = [s for s in samples if s.season == held_out]
        train_freqs = class_frequencies(train_fold)
        best_peak, best_scale = grid_search(train_fold)

        variants = {
            "uniforme": [{"W": 1 / 3, "D": 1 / 3, "L": 1 / 3} for _ in test_fold],
            "frequenze": [train_freqs for _ in test_fold],
            "attuale": [predict(s, DRAW_PEAK_PROBABILITY, DRAW_DECAY_SCALE) for s in test_fold],
            "tuned": [predict(s, best_peak, best_scale) for s in test_fold],
            # A single, targeted change (widen the draw decay only, keep the
            # same peak) that showed up as the per-fold optimum in 5/6 folds
            # below — scored as a FIXED constant here (not re-tuned per fold)
            # to check whether that one specific change generalizes on its
            # own, isolated from the noisier full 2D grid search.
            "scale=400 fisso": [predict(s, DRAW_PEAK_PROBABILITY, 400.0) for s in test_fold],
        }
        for name, preds in variants.items():
            fold_losses[name].append(log_loss(test_fold, preds))
            fold_briers[name].append(brier_score(test_fold, preds))
            fold_accs[name].append(accuracy(test_fold, preds))

        print(
            f"  fold={held_out:<10} n={len(test_fold):<3} "
            f"tuned=({best_peak}/{best_scale:.0f})  "
            f"log loss: attuale={fold_losses['attuale'][-1]:.3f} tuned={fold_losses['tuned'][-1]:.3f}"
        )

    print(f"\nMedia sui {len(seasons)} fold (± deviazione standard):")
    for name in variant_names:
        losses = fold_losses[name]
        mean_loss = sum(losses) / len(losses)
        std_loss = math.sqrt(sum((x - mean_loss) ** 2 for x in losses) / len(losses))
        mean_brier = sum(fold_briers[name]) / len(fold_briers[name])
        mean_acc = sum(fold_accs[name]) / len(fold_accs[name])
        print(
            f"  {name:<12} log loss = {mean_loss:.4f} (±{std_loss:.3f})   "
            f"brier = {mean_brier:.4f}   accuracy = {mean_acc:.3f}"
        )


def main() -> None:
    db: Session = SessionLocal()
    try:
        samples = load_samples(db)
    finally:
        db.close()

    seasons = sorted({s.season for s in samples})
    if len(samples) < 40 or len(seasons) < 3:
        print(
            f"Only {len(samples)} scoreable matches across {len(seasons)} season(s) in the DB — "
            "ingest more seasons for a meaningful backtest (needs >= 3 for cross-validation)."
        )
        return

    print(f"Dataset: {len(samples)} partite Juventus su {len(seasons)} stagioni ({seasons[0]} → {seasons[-1]})")

    # Single chronological holdout (most recent season) — illustrative, but a
    # 38-match sample is noisy; see the cross-validation below for the
    # methodologically sturdier estimate.
    test_season = seasons[-1]
    train = [s for s in samples if s.season != test_season]
    test = [s for s in samples if s.season == test_season]
    print(f"\n{'=' * 70}\nHoldout singolo (ultima stagione: {test_season})\n{'=' * 70}")
    print(f"Train: {len(train)} partite   Test: {len(test)} partite")
    print(f"Distribuzione risultati (train): {class_frequencies(train)}")
    print(f"Distribuzione risultati (test):  {class_frequencies(test)}\n")

    uniform_preds = [{"W": 1 / 3, "D": 1 / 3, "L": 1 / 3} for _ in test]
    empirical_preds = [class_frequencies(train) for _ in test]
    default_preds_test = [predict(s, DRAW_PEAK_PROBABILITY, DRAW_DECAY_SCALE) for s in test]
    best_peak, best_scale = grid_search(train)
    tuned_preds_test = [predict(s, best_peak, best_scale) for s in test]

    score_model("Baseline uniforme (33/33/33)", test, uniform_preds)
    score_model("Baseline frequenze (train)", test, empirical_preds)
    score_model("Elo model (costanti attuali)", test, default_preds_test)
    score_model(f"Elo model (tuned {best_peak}/{best_scale:.0f})", test, tuned_preds_test)

    leave_one_season_out_cv(samples, seasons)

    # Final constants for shipping: refit on the FULL dataset once CV above
    # has already given an honest estimate of how a tuned model generalizes.
    final_peak, final_scale = grid_search(samples)
    print(
        f"\n{'=' * 70}\nCostanti finali (grid search sull'intero dataset): "
        f"DRAW_PEAK_PROBABILITY={final_peak}, DRAW_DECAY_SCALE={final_scale:.0f} "
        f"(attuali: {DRAW_PEAK_PROBABILITY}, {DRAW_DECAY_SCALE:.0f})\n{'=' * 70}"
    )

    print("\nCalibrazione (costanti attuali, intero dataset):")
    all_preds_default = [predict(s, DRAW_PEAK_PROBABILITY, DRAW_DECAY_SCALE) for s in samples]
    calibration_table(samples, all_preds_default)


if __name__ == "__main__":
    main()
