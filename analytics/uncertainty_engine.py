"""
uncertainty_engine.py
=====================
DengueOps AI — Phase 4: Forecast Uncertainty Layer

Converts the single-point forecast in data/forecast_output.json into three
scenario bands — best-case, expected-case, and worst-case — using the RMSE
of the best model from the temporal backtest.

Outputs:
    data/forecast_output.json  (updated in-place with uncertainty fields)

Uncertainty method: RMSE error band
    This is a PROTOTYPE uncertainty estimate, not a calibrated probabilistic
    forecast interval (such as a Bayesian credible interval or a conformal
    prediction interval). It uses the validation RMSE as a symmetric error
    envelope around the point forecast:

        best_case    = max(0, forecast_cases - RMSE)   # optimistic scenario
        expected_case = forecast_cases                  # central estimate
        worst_case   = forecast_cases + RMSE            # pessimistic scenario

    Rationale:
        The RMSE from the temporal backtest measures the typical magnitude of
        the model's errors on genuinely unseen future weeks. Using it as an
        uncertainty band gives a first-order operational sense of how much the
        true case count might differ from the point estimate, without requiring
        a full probabilistic model or bootstrap ensemble.

    Limitations (see README for full discussion):
        - RMSE is not symmetric in probability space; true forecast errors are
          not normally distributed at weekly epidemiological scales.
        - The band does not account for autocorrelated residuals or systematic
          bias during outbreak inflection points.
        - Coverage probability is unknown (the interval may not contain the
          true value 68% of the time, as a 1-sigma Gaussian interval would).
        - For a production system, replace with conformal prediction or a
          bootstrapped GBR ensemble.

    Each scenario case inherits the same reference_cases_4w_rolling so that
    growth factors and risk levels reflect real surge intensity relative to
    the same recent baseline.

Idempotent:
    This script can be run multiple times safely. It removes any existing
    uncertainty_method and uncertainty_scenarios fields before rewriting them.

Usage:
    python analytics/uncertainty_engine.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from forecast_model import classify_risk, compute_growth_factor

# ── I/O paths ─────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
FORECAST_PATH = ROOT / "data" / "forecast_output.json"
VALIDATION_PATH = ROOT / "data" / "validation_metrics.json"


# ─────────────────────────────────────────────────────────────────────────────
# Scenario builder
# ─────────────────────────────────────────────────────────────────────────────

def build_scenario(
    label: str,
    forecast_cases: int,
    reference_cases: float,
) -> dict:
    """
    Build a single uncertainty scenario dict.

    Computes growth factor, risk level, and risk score for a given case count
    relative to the same 4-week rolling reference used in the point forecast.

    Parameters
    ----------
    label : str
        Human-readable label ("Best Case", "Expected Case", "Worst Case").
    forecast_cases : int
        Case count for this scenario (already clamped to >= 0 by caller).
    reference_cases : float
        reference_cases_4w_rolling from the original forecast; held constant
        so all three scenarios are comparable on the same baseline.

    Returns
    -------
    dict
        Scenario entry matching the data contract.
    """
    gf = compute_growth_factor(forecast_cases, reference_cases)
    risk_level, risk_score = classify_risk(gf)
    return {
        "label": label,
        "forecast_cases": forecast_cases,
        "growth_factor": gf,
        "risk_score": risk_score,
        "risk_level": risk_level,
    }


def build_uncertainty_scenarios(
    forecast_cases: int,
    rmse: float,
    reference_cases: float,
) -> dict:
    """
    Build the three scenario band entries from a point forecast and RMSE.

    Parameters
    ----------
    forecast_cases : int
        Central (expected) forecast.
    rmse : float
        Validation RMSE of the best model.
    reference_cases : float
        4-week rolling case average (reference for growth factor).

    Returns
    -------
    dict
        Dict with best_case, expected_case, worst_case scenario entries.
    """
    best_cases = max(0, int(round(forecast_cases - rmse)))
    expected_cases = forecast_cases                           # must match original
    worst_cases = int(round(forecast_cases + rmse))

    return {
        "best_case": build_scenario("Best Case", best_cases, reference_cases),
        "expected_case": build_scenario("Expected Case", expected_cases, reference_cases),
        "worst_case": build_scenario("Worst Case", worst_cases, reference_cases),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Load / save helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}\n"
            "Run the following scripts first:\n"
            "  python analytics/forecast_model.py\n"
            "  python analytics/validation_backtest.py"
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────────────────────────────────────
# Main update logic
# ─────────────────────────────────────────────────────────────────────────────

def apply_uncertainty(
    forecast: dict,
    validation: dict,
) -> dict:
    """
    Inject uncertainty fields into a forecast dict.

    Removes any pre-existing uncertainty_method and uncertainty_scenarios keys
    before rewriting, ensuring idempotency on repeated runs.

    Parameters
    ----------
    forecast : dict
        Contents of forecast_output.json.
    validation : dict
        Contents of validation_metrics.json.

    Returns
    -------
    dict
        Updated forecast dict with uncertainty fields appended.
    """
    # ── Extract inputs ────────────────────────────────────────────────────────
    best_model: str = validation["best_model"]
    rmse: float = validation["metrics"][best_model]["rmse"]

    forecast_cases: int = forecast["forecast_cases"]
    reference_cases: float = float(forecast.get("reference_cases_4w_rolling", 0))

    model_display = {
        "naive": "Naive",
        "moving_average": "MovingAverage",
        "gradient_boosting": "GradientBoostingRegressor",
    }.get(best_model, best_model)

    # ── Remove pre-existing uncertainty fields (idempotency) ──────────────────
    forecast.pop("uncertainty_method", None)
    forecast.pop("uncertainty_scenarios", None)

    # ── Compute uncertainty percentage ────────────────────────────────────────
    uncertainty_pct = round(rmse / forecast_cases * 100, 1) if forecast_cases > 0 else None

    # ── Build and attach uncertainty fields ───────────────────────────────────
    forecast["uncertainty_method"] = {
        "type": "rmse_error_band",
        "source": "time_based_backtest",
        "model": model_display,
        "rmse": rmse,
        "uncertainty_pct": uncertainty_pct,
        "note": (
            "Prototype uncertainty band derived from validation RMSE; "
            "not a calibrated probabilistic interval."
        ),
    }

    forecast["uncertainty_scenarios"] = build_uncertainty_scenarios(
        forecast_cases, rmse, reference_cases
    )

    return forecast


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print()
    print("=" * 62)
    print("  DengueOps AI - Phase 4: Uncertainty Engine")
    print("=" * 62)

    # ── Load inputs ───────────────────────────────────────────────────────────
    print("\n  Loading forecast_output.json ...")
    forecast = load_json(FORECAST_PATH)

    print("  Loading validation_metrics.json ...")
    validation = load_json(VALIDATION_PATH)

    best_model = validation["best_model"]
    rmse = validation["metrics"][best_model]["rmse"]
    forecast_cases = forecast["forecast_cases"]
    reference = float(forecast.get("reference_cases_4w_rolling", 0))

    print(f"\n  Best model       : {best_model}")
    print(f"  Validation RMSE  : {rmse}")
    print(f"  Point forecast   : {forecast_cases} cases  "
          f"(2026 W{forecast['target_epi_week']})")
    print(f"  Reference (4w avg): {reference:.1f} cases")

    # ── Apply uncertainty ─────────────────────────────────────────────────────
    updated_forecast = apply_uncertainty(forecast, validation)
    scenarios = updated_forecast["uncertainty_scenarios"]

    # ── Print scenario summary ────────────────────────────────────────────────
    print()
    print(f"  {'Scenario':<16}  {'Cases':>6}  {'GF':>6}  {'Risk':>10}  {'Score':>6}")
    print("  " + "-" * 50)
    for key in ("best_case", "expected_case", "worst_case"):
        s = scenarios[key]
        print(f"  {s['label']:<16}  {s['forecast_cases']:>6}  "
              f"{s['growth_factor']:>6.3f}  {s['risk_level']:>10}  {s['risk_score']:>6}")

    unc_pct = updated_forecast["uncertainty_method"].get("uncertainty_pct")
    if unc_pct is not None:
        print(f"\n  Uncertainty band : +/- {rmse:.1f} cases  ({unc_pct}% of forecast)")

    # ── Save updated JSON ─────────────────────────────────────────────────────
    save_json(FORECAST_PATH, updated_forecast)
    print(f"\n  Updated: {FORECAST_PATH}")

    print()
    print("=" * 62)
    print("  Uncertainty layer applied.")
    print("=" * 62)
    print()


if __name__ == "__main__":
    main()
