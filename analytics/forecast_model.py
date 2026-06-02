"""
forecast_model.py
=================
DengueOps AI — Phase 3: Final Model Training and Forecast Generation

Trains a GradientBoostingRegressor on the full feature matrix and generates
a 14-day ahead forecast from the most recent available feature row.

Outputs:
    data/forecast_output.json

Design decisions:
    - The final forecast model is trained on ALL available feature rows (not just
      the 80% training split used in backtesting). Using all data for the final
      deployed model is standard practice once the backtest has validated that
      the approach generalises.
    - Forecast target is target_cases_next_2w (14-day / 2-week horizon).
    - Risk classification uses growth factor relative to the recent 4-week rolling
      mean of cases. This reflects trend acceleration, not absolute case count.

Usage:
    python analytics/forecast_model.py
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from feature_engineering import (
    build_features,
    FEATURE_COLUMNS,
    DEFAULT_OUTPUT_PATH as FEATURES_CSV,
)

# ── Output path ───────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
FORECAST_OUTPUT = ROOT / "data" / "forecast_output.json"

# ── Model configuration ───────────────────────────────────────────────────────
TARGET_COL = "target_cases_next_2w"
HORIZON_DAYS = 14
RANDOM_STATE = 42

GBR_PARAMS: dict = {
    "n_estimators": 200,
    "learning_rate": 0.05,
    "max_depth": 4,
    "min_samples_leaf": 3,
    "subsample": 0.8,
    "random_state": RANDOM_STATE,
}

# ── Risk thresholds ───────────────────────────────────────────────────────────
# Growth factor = forecast_cases / recent_reference_cases
# Represents relative surge intensity above recent baseline.
RISK_THRESHOLDS = [
    (1.10, "Low"),
    (1.50, "Moderate"),
    (2.00, "High"),
    (float("inf"), "Critical"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Risk classification
# ─────────────────────────────────────────────────────────────────────────────

def classify_risk(growth_factor: float) -> tuple[str, int]:
    """
    Classify risk level and compute risk score (0–100) from growth factor.

    Risk levels:
        Low      : growth_factor < 1.10  (stable or slightly declining)
        Moderate : 1.10 <= growth_factor < 1.50
        High     : 1.50 <= growth_factor < 2.00
        Critical : growth_factor >= 2.00

    Risk score mapping (piece-wise linear, 0–100):
        The score increases monotonically with growth_factor. Thresholds match
        the risk level boundaries so that the score transitions align with levels:
            gf=0.0 → score=0
            gf=1.0 → score≈32
            gf=1.1 → score=35  (Low ceiling)
            gf=1.5 → score=60  (Moderate ceiling)
            gf=2.0 → score=85  (High ceiling)
            gf=3.0 → score=97  (Critical, approaching cap)

    Parameters
    ----------
    growth_factor : float
        Ratio of forecast_cases to recent_reference_cases.

    Returns
    -------
    (risk_level, risk_score) : tuple[str, int]
    """
    gf = max(0.0, growth_factor)

    # Piece-wise linear score bands
    if gf < 1.0:
        score = gf * 32.0                              # 0  → 32
    elif gf < 1.10:
        score = 32.0 + (gf - 1.0) / 0.10 * 3.0       # 32 → 35
    elif gf < 1.50:
        score = 35.0 + (gf - 1.10) / 0.40 * 25.0     # 35 → 60
    elif gf < 2.00:
        score = 60.0 + (gf - 1.50) / 0.50 * 25.0     # 60 → 85
    else:
        score = 85.0 + (gf - 2.00) * 10.0             # 85+, diminishing

    risk_score = max(0, min(100, round(score)))

    # Assign level from threshold table
    risk_level = "Critical"   # default if all thresholds exceeded
    for threshold, level in RISK_THRESHOLDS:
        if gf < threshold:
            risk_level = level
            break

    return risk_level, risk_score


def compute_growth_factor(forecast_cases: float, reference_cases: float) -> float:
    """
    Ratio of forecast_cases to reference_cases.
    Returns 1.0 (neutral) if reference is zero or negative.
    Clamped to [0.01, 10.0] to prevent extreme outliers in edge cases.
    """
    if reference_cases <= 0:
        return 1.0
    return max(0.01, min(10.0, round(forecast_cases / reference_cases, 3)))


def advance_epi_week(epi_year: int, epi_week: int, weeks: int) -> tuple[int, int]:
    """
    Advance an (epi_year, epi_week) pair by `weeks` weeks.
    Handles year rollover (week 52 + 1 = next year week 1).
    Assumes 52-week years for simplicity (demo context).
    """
    total_week = epi_week + weeks
    if total_week > 52:
        return epi_year + 1, total_week - 52
    return epi_year, total_week


# ─────────────────────────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────────────────────────

def load_feature_matrix() -> pd.DataFrame:
    """Load model_features.csv or build it on demand."""
    if Path(FEATURES_CSV).exists():
        df = pd.read_csv(FEATURES_CSV)
        return df.sort_values(["epi_year", "epi_week"]).reset_index(drop=True)
    print("  model_features.csv not found — building features now...")
    df, _ = build_features()
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Model training
# ─────────────────────────────────────────────────────────────────────────────

def train_final_model(df: pd.DataFrame) -> GradientBoostingRegressor:
    """
    Train the final GBR model on the complete feature matrix.

    Unlike the backtest (which uses only 80% of rows), the final forecast model
    is trained on all available data. This gives the model the most up-to-date
    pattern knowledge when generating the operational forecast — including the
    most recent 2026 early-warning rise in the data.

    Parameters
    ----------
    df : pd.DataFrame
        Full feature matrix from build_features(), sorted chronologically.

    Returns
    -------
    GradientBoostingRegressor
        Fitted model ready for prediction.
    """
    X = df[FEATURE_COLUMNS].values
    y = df[TARGET_COL].values

    model = GradientBoostingRegressor(**GBR_PARAMS)
    model.fit(X, y)
    return model


# ─────────────────────────────────────────────────────────────────────────────
# Forecast generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_forecast(
    df: pd.DataFrame,
    model: GradientBoostingRegressor,
) -> dict:
    """
    Generate a 14-day ahead forecast from the latest available feature row.

    The "latest feature row" is the most recent row in the sorted feature matrix.
    Its target_cases_next_2w was computed as cases[t+2], so the forecast corresponds
    to the dengue case count expected 2 epi-weeks from the latest observation.

    Baseline forecasts (naive and moving average) are also generated from the
    same latest row for comparison.

    Parameters
    ----------
    df : pd.DataFrame
        Full sorted feature matrix.
    model : GradientBoostingRegressor
        Fitted model from train_final_model().

    Returns
    -------
    dict
        Forecast output dict matching the data contract for forecast_output.json.
    """
    latest = df.iloc[-1]

    # ── ML forecast ───────────────────────────────────────────────────────────
    x_latest = latest[FEATURE_COLUMNS].values.reshape(1, -1)
    ml_forecast_raw = float(model.predict(x_latest)[0])
    ml_forecast = max(0, round(ml_forecast_raw))

    # ── Baseline forecasts (same latest row, no model needed) ─────────────────
    naive_forecast = max(0, int(round(latest["cases_lag_1w"])))
    ma_forecast = max(0, int(round(latest["cases_rolling_4w"])))

    # ── Reference for growth factor: 4-week rolling mean is a stable recent signal
    reference_cases = float(latest["cases_rolling_4w"])
    growth_factor = compute_growth_factor(ml_forecast, reference_cases)
    risk_level, risk_score = classify_risk(growth_factor)

    # ── Target epi week: latest known week + 2 weeks ──────────────────────────
    latest_year = int(latest["epi_year"])
    latest_week = int(latest["epi_week"])
    target_year, target_week = advance_epi_week(latest_year, latest_week, 2)

    return {
        "forecast_id": 1,
        "date_generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "latest_known_epi_year": latest_year,
        "latest_known_epi_week": latest_week,
        "target_epi_year": target_year,
        "target_epi_week": target_week,
        "horizon_days": HORIZON_DAYS,
        "city": str(latest["city"]),
        "forecast_cases": ml_forecast,
        "growth_factor": growth_factor,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "model_name": "GradientBoostingRegressor",
        "model_params": GBR_PARAMS,
        "features_used": FEATURE_COLUMNS,
        "reference_cases_4w_rolling": round(reference_cases, 1),
        "latest_observed_cases": int(latest["cases"]),
        "baseline_context": {
            "naive_forecast": naive_forecast,
            "moving_average_forecast": ma_forecast,
        },
        "notes": [
            "Forecast trained on all available feature rows (full data, no holdout).",
            "Baseline forecasts use feature values from the same latest row.",
            "Growth factor computed relative to cases_rolling_4w (4-week rolling mean).",
            "All values are based on synthetic/demo data. Not a real operational forecast.",
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print()
    print("=" * 62)
    print("  DengueOps AI - Phase 3: Final Forecast")
    print("=" * 62)

    # ── Load data ─────────────────────────────────────────────────────────────
    print("\n  Loading feature matrix...")
    df = load_feature_matrix()
    latest = df.iloc[-1]
    print(f"    Rows: {len(df)}")
    print(f"    Latest row: {int(latest['epi_year'])} W{int(latest['epi_week'])}  "
          f"cases={int(latest['cases'])}")

    # ── Train model ───────────────────────────────────────────────────────────
    print("\n  Training GradientBoostingRegressor on all data...")
    print(f"    n_estimators={GBR_PARAMS['n_estimators']}, "
          f"learning_rate={GBR_PARAMS['learning_rate']}, "
          f"max_depth={GBR_PARAMS['max_depth']}")
    model = train_final_model(df)
    print(f"    Training complete. Features: {len(FEATURE_COLUMNS)}")

    # ── Generate forecast ─────────────────────────────────────────────────────
    print("\n  Generating 14-day ahead forecast...")
    forecast = generate_forecast(df, model)

    # ── Print forecast summary ────────────────────────────────────────────────
    print()
    print(f"  Forecast target    : "
          f"{forecast['target_epi_year']} W{forecast['target_epi_week']} "
          f"(+{HORIZON_DAYS} days)")
    print(f"  Forecasted cases   : {forecast['forecast_cases']:,}")
    print(f"  Growth factor      : {forecast['growth_factor']:.3f}x "
          f"(ref: {forecast['reference_cases_4w_rolling']:.1f} cases / 4w avg)")
    print(f"  Risk level         : {forecast['risk_level']}")
    print(f"  Risk score         : {forecast['risk_score']} / 100")
    print()
    print(f"  Baseline comparison:")
    print(f"    Naive forecast    : {forecast['baseline_context']['naive_forecast']:,}")
    print(f"    Moving avg (4w)   : {forecast['baseline_context']['moving_average_forecast']:,}")
    print(f"    ML (GBR) forecast : {forecast['forecast_cases']:,}")

    # ── Save JSON ─────────────────────────────────────────────────────────────
    FORECAST_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(FORECAST_OUTPUT, "w", encoding="utf-8") as fh:
        json.dump(forecast, fh, indent=2, ensure_ascii=False)

    print(f"\n  Saved: {FORECAST_OUTPUT}")
    print()
    print("=" * 62)
    print("  Forecast generation complete.")
    print("=" * 62)
    print()


if __name__ == "__main__":
    main()
