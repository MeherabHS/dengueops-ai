"""
validation_backtest.py
======================
DengueOps AI — Phase 3: Temporal Backtesting and Baseline Comparison

Evaluates three forecasting approaches on a strictly chronological holdout set:
    1. Naive (Last Known)        — predict using cases_lag_1w from the feature row
    2. Moving Average            — predict using cases_rolling_4w from the feature row
    3. GradientBoostingRegressor — trained on FEATURE_COLUMNS from feature_engineering.py

Outputs:
    data/validation_metrics.json

Why time-based validation?
    Random train/test splits are inappropriate for time series data. If training
    data includes future observations (e.g., 2026 week 12 in train, 2025 week 40
    in test), the model can memorise future patterns and produce unrealistically
    strong test metrics that collapse when deployed on genuinely unseen future data.

    A strict chronological holdout — using the first 80% of rows for training and
    the remaining 20% for testing — guarantees that every test prediction is made
    using only information that would have been available at that point in time.
    This mimics real operational deployment conditions.

Usage:
    python analytics/validation_backtest.py
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

# ── Path setup: allow importing from the analytics/ sibling directory ─────────
sys.path.insert(0, str(Path(__file__).parent))
from feature_engineering import (
    build_features,
    FEATURE_COLUMNS,
    DEFAULT_OUTPUT_PATH as FEATURES_CSV,
)

# ── Output path ───────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
VALIDATION_OUTPUT = ROOT / "data" / "validation_metrics.json"

# ── Backtest configuration ─────────────────────────────────────────────────────
TRAIN_FRACTION = 0.80        # 80% train / 20% test chronological split
TARGET_COL = "target_cases_next_2w"   # 14-day ahead forecast target
RANDOM_STATE = 42

# GBR hyperparameters
GBR_PARAMS: dict = {
    "n_estimators": 200,
    "learning_rate": 0.05,
    "max_depth": 4,
    "min_samples_leaf": 3,
    "subsample": 0.8,
    "random_state": RANDOM_STATE,
}


# ─────────────────────────────────────────────────────────────────────────────
# Metric utilities
# ─────────────────────────────────────────────────────────────────────────────

def compute_mae(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Mean Absolute Error."""
    return float(np.mean(np.abs(actual - predicted)))


def compute_rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Root Mean Squared Error."""
    return float(math.sqrt(np.mean((actual - predicted) ** 2)))


def compute_mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """
    Mean Absolute Percentage Error, computed only on rows where actual > 0.
    Returns NaN if no valid rows remain.
    """
    mask = actual > 0
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100)


def compute_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
    """Compute MAE, RMSE, MAPE and return as a dict with values rounded to 2 dp."""
    return {
        "mae": round(compute_mae(actual, predicted), 2),
        "rmse": round(compute_rmse(actual, predicted), 2),
        "mape": round(compute_mape(actual, predicted), 2),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Load / build feature matrix
# ─────────────────────────────────────────────────────────────────────────────

def load_feature_matrix() -> pd.DataFrame:
    """
    Load model_features.csv if it exists, otherwise build it on the fly.
    The returned DataFrame is guaranteed to be sorted by (epi_year, epi_week).
    """
    if Path(FEATURES_CSV).exists():
        df = pd.read_csv(FEATURES_CSV)
        df = df.sort_values(["epi_year", "epi_week"]).reset_index(drop=True)
        return df

    print("  model_features.csv not found — building features now...")
    df, _ = build_features()
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Baseline predictions
# ─────────────────────────────────────────────────────────────────────────────

def predict_naive(test_df: pd.DataFrame) -> np.ndarray:
    """
    Naive forecast: predict the target using the most recent known case count
    (cases_lag_1w), which represents last week's observed cases.

    Rationale: this baseline tests whether any model adds value over simply
    assuming the current trajectory continues. If the ML model cannot beat
    this baseline, it provides no useful signal.
    """
    return test_df["cases_lag_1w"].values.astype(float)


def predict_moving_average(test_df: pd.DataFrame) -> np.ndarray:
    """
    Moving average forecast: predict using the 4-week rolling mean of past cases.

    This baseline smooths out week-to-week noise and represents the most recent
    short-term trend. It is harder to beat than the naive baseline during stable
    or slowly trending periods.
    """
    return test_df["cases_rolling_4w"].values.astype(float)


# ─────────────────────────────────────────────────────────────────────────────
# Backtest runner
# ─────────────────────────────────────────────────────────────────────────────

def run_backtest(df: pd.DataFrame) -> dict:
    """
    Run temporal backtest with naive, moving average, and GBR models.

    Split strategy:
        - Data is already sorted by (epi_year, epi_week).
        - Rows 0 to train_cutoff-1 are used for training.
        - Rows train_cutoff to end are used for testing.
        - No shuffling occurs at any step. This preserves temporal ordering.

    Parameters
    ----------
    df : pd.DataFrame
        Feature matrix from build_features(), sorted chronologically.

    Returns
    -------
    dict
        Backtest results including metrics per model and actual_vs_predicted rows.
    """
    n_rows = len(df)
    train_cutoff = int(n_rows * TRAIN_FRACTION)   # e.g. int(121 * 0.80) = 96
    test_start = train_cutoff

    train_df = df.iloc[:train_cutoff].copy()
    test_df = df.iloc[test_start:].copy()

    # ── Feature matrix and targets ────────────────────────────────────────────
    X_train = train_df[FEATURE_COLUMNS].values
    y_train = train_df[TARGET_COL].values

    X_test = test_df[FEATURE_COLUMNS].values
    y_test = test_df[TARGET_COL].values

    # ── Train GBR ─────────────────────────────────────────────────────────────
    # random_state is fixed for full reproducibility. n_estimators and
    # learning_rate are conservative to avoid overfitting on a small dataset.
    gbr = GradientBoostingRegressor(**GBR_PARAMS)
    gbr.fit(X_train, y_train)
    y_pred_gbr = np.maximum(0, gbr.predict(X_test))   # clamp negative predictions

    # ── Baselines ─────────────────────────────────────────────────────────────
    y_pred_naive = predict_naive(test_df)
    y_pred_ma = predict_moving_average(test_df)

    # ── Metrics ───────────────────────────────────────────────────────────────
    metrics = {
        "naive": compute_metrics(y_test, y_pred_naive),
        "moving_average": compute_metrics(y_test, y_pred_ma),
        "gradient_boosting": compute_metrics(y_test, y_pred_gbr),
    }

    # ── Determine best model by MAE ───────────────────────────────────────────
    best_model = min(metrics, key=lambda k: metrics[k]["mae"])

    # ── Actual vs predicted table ─────────────────────────────────────────────
    actual_vs_predicted = []
    for i, (_, row) in enumerate(test_df.iterrows()):
        actual_vs_predicted.append({
            "epi_year": int(row["epi_year"]),
            "epi_week": int(row["epi_week"]),
            "actual": int(round(y_test[i])),
            "naive_pred": int(round(y_pred_naive[i])),
            "moving_average_pred": int(round(y_pred_ma[i])),
            "ml_pred": int(round(y_pred_gbr[i])),
        })

    return {
        "target": TARGET_COL,
        "validation_design": "time_based_holdout_final_20_percent",
        "train_rows": int(train_cutoff),
        "test_rows": int(n_rows - train_cutoff),
        "train_period": {
            "epi_year_start": int(df.iloc[0]["epi_year"]),
            "epi_week_start": int(df.iloc[0]["epi_week"]),
            "epi_year_end": int(df.iloc[train_cutoff - 1]["epi_year"]),
            "epi_week_end": int(df.iloc[train_cutoff - 1]["epi_week"]),
        },
        "test_period": {
            "epi_year_start": int(df.iloc[test_start]["epi_year"]),
            "epi_week_start": int(df.iloc[test_start]["epi_week"]),
            "epi_year_end": int(df.iloc[-1]["epi_year"]),
            "epi_week_end": int(df.iloc[-1]["epi_week"]),
        },
        "metrics": metrics,
        "best_model": best_model,
        "gbr_params": GBR_PARAMS,
        "feature_count": len(FEATURE_COLUMNS),
        "features_used": FEATURE_COLUMNS,
        "actual_vs_predicted": actual_vs_predicted,
        "notes": [
            "Validation uses final chronological 20% of available feature rows.",
            "Time-based holdout only — no random shuffling at any step.",
            "Results are based on synthetic/demo aggregate data generated for prototype testing.",
            "This validates pipeline behaviour and feature engineering correctness, "
            "not deployment-grade epidemiological accuracy.",
            "Real validation would require multi-year validated DGHS/IEDCR surveillance data.",
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print()
    print("=" * 62)
    print("  DengueOps AI - Phase 3: Temporal Backtest")
    print("=" * 62)

    # ── Load data ─────────────────────────────────────────────────────────────
    print("\n  Loading feature matrix...")
    df = load_feature_matrix()
    print(f"    Rows: {len(df)}  |  Cols: {len(df.columns)}")
    print(f"    Period: {df.iloc[0]['epi_year']} W{df.iloc[0]['epi_week']} "
          f"to {df.iloc[-1]['epi_year']} W{df.iloc[-1]['epi_week']}")

    # ── Run backtest ──────────────────────────────────────────────────────────
    print("\n  Running temporal backtest...")
    print(f"    Target         : {TARGET_COL} (14-day / 2-week ahead)")
    print(f"    Split          : {int(TRAIN_FRACTION*100)}% train / "
          f"{100 - int(TRAIN_FRACTION*100)}% test (chronological)")

    results = run_backtest(df)

    # ── Print metrics ─────────────────────────────────────────────────────────
    print(f"\n  Train period  : "
          f"{results['train_period']['epi_year_start']} "
          f"W{results['train_period']['epi_week_start']} "
          f"to {results['train_period']['epi_year_end']} "
          f"W{results['train_period']['epi_week_end']} "
          f"({results['train_rows']} rows)")
    print(f"  Test period   : "
          f"{results['test_period']['epi_year_start']} "
          f"W{results['test_period']['epi_week_start']} "
          f"to {results['test_period']['epi_year_end']} "
          f"W{results['test_period']['epi_week_end']} "
          f"({results['test_rows']} rows)")

    print("\n  Metrics (target: cases 2 weeks ahead):")
    header = f"  {'Model':<26}  {'MAE':>8}  {'RMSE':>8}  {'MAPE (%)':>10}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for model_name, m in results["metrics"].items():
        tag = " <-- best" if model_name == results["best_model"] else ""
        print(f"  {model_name:<26}  {m['mae']:>8.1f}  {m['rmse']:>8.1f}  "
              f"{m['mape']:>10.1f}{tag}")

    print(f"\n  Best model by MAE: {results['best_model']}")

    # ── Save JSON ─────────────────────────────────────────────────────────────
    VALIDATION_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(VALIDATION_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n  Saved: {VALIDATION_OUTPUT}")
    print()
    print("=" * 62)
    print("  Backtest complete.")
    print("=" * 62)
    print()


if __name__ == "__main__":
    main()
