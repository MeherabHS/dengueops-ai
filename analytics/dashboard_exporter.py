"""
dashboard_exporter.py
=====================
DengueOps AI — Phase 6: Dashboard-Ready JSON Exporter

Reads all analytics pipeline outputs and produces three clean,
frontend-friendly JSON files for the Next.js dashboard.

Philosophy:
    The Python pipeline is not the evaluator-facing product. It is the
    analytics engine. All relevant outputs are exported into dashboard-ready
    JSON files and visualised in the Next.js dashboard. Evaluators do not
    need to inspect terminal logs or raw intermediate files.

Inputs  (must exist before running):
    data/forecast_output.json
    data/validation_metrics.json
    data/directives.json
    data/zones.json
    data/facilities.json
    data/inventory.json
    data/dengue_cases.csv       (optional, for case_trend chart)
    data/climate_data.csv       (optional, for case_trend rainfall overlay)
    data/model_features.csv     (optional, feature coverage info)

Outputs:
    data/dashboard_summary.json  — headline metrics + uncertainty + model evidence
    data/model_comparison.json   — model table with roles + selection rationale
    data/chart_data.json         — all chart arrays for dashboard visualisation

Usage:
    python analytics/dashboard_exporter.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT         = Path(__file__).resolve().parent.parent
DATA_DIR     = ROOT / "data"

FORECAST_PATH   = DATA_DIR / "forecast_output.json"
VALIDATION_PATH = DATA_DIR / "validation_metrics.json"
DIRECTIVES_PATH = DATA_DIR / "directives.json"
ZONES_PATH      = DATA_DIR / "zones.json"
FACILITIES_PATH = DATA_DIR / "facilities.json"
INVENTORY_PATH  = DATA_DIR / "inventory.json"
CASES_PATH      = DATA_DIR / "dengue_cases.csv"
CLIMATE_PATH    = DATA_DIR / "climate_data.csv"
FEATURES_PATH   = DATA_DIR / "model_features.csv"

DASHBOARD_SUMMARY_PATH = DATA_DIR / "dashboard_summary.json"
MODEL_COMPARISON_PATH  = DATA_DIR / "model_comparison.json"
CHART_DATA_PATH        = DATA_DIR / "chart_data.json"

# ── Required inputs ───────────────────────────────────────────────────────────
REQUIRED_INPUTS = [
    FORECAST_PATH,
    VALIDATION_PATH,
    DIRECTIVES_PATH,
]

# ── I/O helpers ───────────────────────────────────────────────────────────────

def load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(
            f"Required input not found: {path}\n"
            "Run the full pipeline first:\n"
            "  python analytics/run_pipeline.py"
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_csv_safe(path: Path) -> pd.DataFrame | None:
    """Load a CSV, returning None if absent (optional inputs)."""
    if not path.exists():
        return None
    return pd.read_csv(path)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Output 1: dashboard_summary.json ─────────────────────────────────────────

def build_dashboard_summary(
    forecast: dict,
    validation: dict,
    directives: dict,
) -> dict:
    """
    Build the headline-level summary consumed by the dashboard's hero section,
    scenario selector, and model evidence panels.
    """
    scenarios = forecast.get("uncertainty_scenarios", {})
    expected  = scenarios.get("expected_case", {})
    best      = scenarios.get("best_case", {})
    worst     = scenarios.get("worst_case", {})

    # ── Model evidence calculations ───────────────────────────────────────────
    metrics      = validation.get("metrics", {})
    naive_mae    = float(metrics.get("naive", {}).get("mae", 0))
    ma_mae       = float(metrics.get("moving_average", {}).get("mae", 0))
    gbr_mae      = float(metrics.get("gradient_boosting", {}).get("mae", 0))
    gbr_rmse     = float(metrics.get("gradient_boosting", {}).get("rmse", 0))

    mae_vs_naive = round((1 - gbr_mae / naive_mae) * 100, 1) if naive_mae > 0 else None
    mae_vs_ma    = round((1 - gbr_mae / ma_mae) * 100, 1)    if ma_mae > 0    else None

    # ── Directives summary ────────────────────────────────────────────────────
    s = directives.get("summary", {})

    return {
        "project": {
            "title":       "DengueOps AI",
            "subtitle":    "Simulation-Based Dengue Surge Preparedness Decision Support"
                           " for Dhaka South",
            "track":       "Health Data Analytics & Predictive Systems",
            "conference":  "IEEE ICADHI",
            "mode":        "Synthetic Demonstration Dataset",
            "last_updated": forecast.get("date_generated", ""),
            "data_status": "No patient-level data used. All readiness values are synthetic.",
        },
        "headline_metrics": {
            "forecast_cases":                int(forecast.get("forecast_cases", 0)),
            "growth_factor":                 float(forecast.get("growth_factor", 1.0)),
            "risk_level":                    forecast.get("risk_level", ""),
            "risk_score":                    int(forecast.get("risk_score", 0)),
            "target_epi_week":               forecast.get("target_epi_week"),
            "target_epi_year":               forecast.get("target_epi_year"),
            "highest_priority_zone":         s.get("highest_priority_zone", ""),
            "highest_pressure_facility":     s.get("highest_pressure_facility", ""),
            "critical_supply_alerts":        int(s.get("critical_supply_alerts", 0)),
            "facilities_with_expected_bed_gap": int(s.get("facilities_with_expected_bed_gap", 0)),
            "total_facilities":              int(s.get("total_facilities", 0)),
            "total_public_government_anchors": int(s.get("total_public_government_anchors", 0)),
            "critical_priority_zones":       int(s.get("critical_priority_zones", 0)),
        },
        "uncertainty": {
            "best_case":     best,
            "expected_case": expected,
            "worst_case":    worst,
            "method":        forecast.get("uncertainty_method", "rmse_derived_bands"),
            "method_note": (
                "RMSE-derived prototype uncertainty band (forecast ± validation RMSE). "
                "Not a calibrated probabilistic interval. "
                f"Band width: ±{round(gbr_rmse, 1)} cases ({round(gbr_rmse / max(1, forecast.get('forecast_cases', 1)) * 100, 1)}% of forecast)."
            ),
        },
        "model_evidence": {
            "best_model":                     validation.get("best_model", "gradient_boosting"),
            "best_model_display":             "Gradient Boosting Regressor",
            "best_model_reason":              "Lowest MAE and RMSE under time-based chronological validation.",
            "validation_design":              validation.get("validation_design", "time_based_holdout"),
            "train_rows":                     validation.get("train_rows"),
            "test_rows":                      validation.get("test_rows"),
            "gbr_mae":                        gbr_mae,
            "gbr_rmse":                       gbr_rmse,
            "mae_reduction_vs_naive_pct":     mae_vs_naive,
            "mae_reduction_vs_moving_average_pct": mae_vs_ma,
            "disclaimer": (
                "Validation is performed on synthetic data. "
                "Results demonstrate prototype pipeline correctness, not real-world accuracy."
            ),
        },
        "operational_summary": {
            "total_recommendations":          int(s.get("total_recommendations", 0)),
            "critical_priority_zones":        int(s.get("critical_priority_zones", 0)),
            "facilities_with_expected_bed_gap": int(s.get("facilities_with_expected_bed_gap", 0)),
            "facilities_with_worst_case_bed_gap": int(s.get("facilities_with_worst_case_bed_gap", 0)),
            "critical_supply_alerts":         int(s.get("critical_supply_alerts", 0)),
            "highest_priority_zone":          s.get("highest_priority_zone", ""),
            "highest_pressure_facility":      s.get("highest_pressure_facility", ""),
        },
        "ethics_and_assumptions": [
            "Prototype uses aggregated/synthetic data only.",
            "No patient-level data is collected or processed.",
            "Real facility names (DMCH, SSMC, Mugda, NIBPS) are used as public-sector "
            "anchor profiles only. Bed, stock, and readiness values are synthetic.",
            "Facility stock and bed readiness values are synthetic demonstration values.",
            "Spatial case allocation is a heuristic; zone-level counts are not "
            "precision estimates.",
            "Outputs are advisory and require human review before any operational action.",
        ],
    }


# ── Output 2: model_comparison.json ───────────────────────────────────────────

MODEL_META: dict[str, dict] = {
    "naive": {
        "model_name": "Naive Baseline",
        "role":       "Predicts next value = last observed value. "
                      "Establishes the minimum bar any model must exceed.",
    },
    "moving_average": {
        "model_name": "Moving Average Baseline (4-week)",
        "role":       "Predicts next value = rolling 4-week mean. "
                      "Tests whether trend smoothing adds value over naive.",
    },
    "gradient_boosting": {
        "model_name": "Gradient Boosting Regressor (scikit-learn)",
        "role":       "Selected tabular ML model. Trained on lag features, "
                      "rolling statistics, and seasonal encodings.",
    },
}


def build_model_comparison(validation: dict) -> dict:
    """
    Build a clean model comparison table with rationale text.
    Used by the Technical Validation view and ModelEvaluationPanel.
    """
    metrics  = validation.get("metrics", {})
    best_key = validation.get("best_model", "gradient_boosting")

    models_out = []
    for key, meta in MODEL_META.items():
        m = metrics.get(key, {})
        models_out.append({
            "model_key":  key,
            "model_name": meta["model_name"],
            "role":       meta["role"],
            "is_selected": key == best_key,
            "mae":  round(float(m.get("mae",  0)), 2),
            "rmse": round(float(m.get("rmse", 0)), 2),
            "mape": round(float(m.get("mape", 0)), 2),
        })

    # Compute improvement ratios
    gbr = metrics.get("gradient_boosting", {})
    naive = metrics.get("naive", {})
    gbr_mae  = float(gbr.get("mae", 1))
    naive_mae = float(naive.get("mae", 1))

    return {
        "target":            validation.get("target", "target_cases_next_2w"),
        "horizon":           "14 days (2 weeks ahead)",
        "validation_design": validation.get("validation_design", "time_based_holdout"),
        "train_period":      validation.get("train_period", {}),
        "test_period":       validation.get("test_period", {}),
        "best_model":        best_key,
        "models":            models_out,
        "selection_explanation": (
            "GradientBoostingRegressor was selected because it achieved the lowest MAE "
            f"({round(gbr_mae, 1)}) and RMSE under chronological time-based validation — "
            f"{round((1 - gbr_mae / naive_mae) * 100, 1)}% lower MAE than the Naive baseline. "
            "The project does not claim algorithmic novelty; the model is used as a "
            "practical forecasting component in a decision-support prototype."
        ),
        "leakage_prevention": (
            "All features use shift(1) before rolling windows. Target columns are "
            "excluded from training features. Train/test split is strictly chronological."
        ),
        "notes": validation.get("notes", []),
    }


# ── Output 3: chart_data.json ─────────────────────────────────────────────────

def build_chart_data(
    forecast: dict,
    validation: dict,
    directives: dict,
    cases_df: pd.DataFrame | None,
    climate_df: pd.DataFrame | None,
) -> dict:
    """
    Build all chart data arrays. Each key maps to a flat array of records
    that a Recharts component can consume directly.
    """
    directive_list = directives.get("directives", [])
    metrics        = validation.get("metrics", {})
    scenarios      = forecast.get("uncertainty_scenarios", {})

    # ── 1. Actual vs Predicted ────────────────────────────────────────────────
    avp_raw = validation.get("actual_vs_predicted", [])
    actual_vs_predicted = [
        {
            "label":            f"{row['epi_year']}-W{int(row['epi_week']):02d}",
            "actual":           int(row["actual"]),
            "naive":            int(row.get("naive_pred", 0)),
            "moving_average":   int(row.get("moving_average_pred", 0)),
            "gradient_boosting": int(row.get("ml_pred", 0)),
        }
        for row in avp_raw
    ]

    # ── 2. Model error bars ───────────────────────────────────────────────────
    model_error_bars = [
        {
            "model": MODEL_META.get(key, {}).get("model_name", key),
            "mae":   round(float(m.get("mae",  0)), 1),
            "rmse":  round(float(m.get("rmse", 0)), 1),
        }
        for key, m in metrics.items()
    ]

    # ── 3. Uncertainty scenarios ──────────────────────────────────────────────
    uncertainty_scenarios = [
        {
            "scenario":       v.get("label", k),
            "forecast_cases": int(v.get("forecast_cases", 0)),
            "growth_factor":  round(float(v.get("growth_factor", 1)), 3),
            "risk_score":     int(v.get("risk_score", 0)),
            "risk_level":     v.get("risk_level", ""),
        }
        for k, v in scenarios.items()
    ]

    # ── 4. Zone priority (deduplicated, one row per zone) ─────────────────────
    seen_zones: dict[str, dict] = {}
    for d in directive_list:
        zid = d["zone_id"]
        if zid not in seen_zones:
            seen_zones[zid] = {
                "zone_name":       d["zone_name"],
                "priority_score":  int(d["priority_score"]),
                # Use zone-total allocated cases (not facility share)
                "allocated_cases": round(
                    float(d.get("zone_allocated_cases_expected",
                                d.get("allocated_cases_expected", 0))), 1
                ),
                "risk_category":   d["priority_category"],
            }
    zone_priority = sorted(
        seen_zones.values(),
        key=lambda x: x["priority_score"],
        reverse=True,
    )

    # ── 5. Supply depletion (NS1 and IVF per facility) ────────────────────────
    supply_depletion: list[dict] = []
    seen_fac_items: set[str] = set()
    for d in directive_list:
        fid = d["facility_id"]

        # NS1
        key_ns1 = f"{fid}:NS1"
        if key_ns1 not in seen_fac_items and d.get("sdh_ns1_expected") is not None:
            seen_fac_items.add(key_ns1)
            supply_depletion.append({
                "facility_name":  d["facility_name"],
                "facility_id":    fid,
                "zone_name":      d["zone_name"],
                "item_name":      "NS1/RDT Kit",
                "sdh_best":       d.get("sdh_ns1_best"),
                "sdh_expected":   d["sdh_ns1_expected"],
                "sdh_worst":      d.get("sdh_ns1_worst"),
                "threshold_days": 7,
            })

        # IV Fluid
        key_ivf = f"{fid}:IVF"
        if key_ivf not in seen_fac_items and d.get("sdh_iv_fluid_expected") is not None:
            seen_fac_items.add(key_ivf)
            supply_depletion.append({
                "facility_name":  d["facility_name"],
                "facility_id":    fid,
                "zone_name":      d["zone_name"],
                "item_name":      "IV Fluid (500ml)",
                "sdh_best":       d.get("sdh_iv_fluid_best"),
                "sdh_expected":   d["sdh_iv_fluid_expected"],
                "sdh_worst":      d.get("sdh_iv_fluid_worst"),
                "threshold_days": 5,
            })

    # Sort by expected SDH ascending (most stressed first)
    supply_depletion.sort(key=lambda x: x["sdh_expected"] or 999)

    # ── 6. Bed gap (per facility) ─────────────────────────────────────────────
    seen_fac_bed: set[str] = set()
    bed_gap: list[dict] = []
    for d in directive_list:
        fid = d["facility_id"]
        if fid in seen_fac_bed:
            continue
        seen_fac_bed.add(fid)
        bed_gap.append({
            "facility_name":     d["facility_name"],
            "facility_id":       fid,
            "zone_name":         d["zone_name"],
            "total_beds":        int(d.get("total_dengue_beds", 0)),
            "occupied_beds":     int(d.get("occupied_dengue_beds", 0)),
            "bed_gap_best":      round(float(d.get("bed_gap_best", 0)), 1),
            "bed_gap_expected":  round(float(d.get("bed_gap_expected", 0)), 1),
            "bed_gap_worst":     round(float(d.get("bed_gap_worst", 0)), 1),
        })
    # Sort by expected bed gap descending
    bed_gap.sort(key=lambda x: x["bed_gap_expected"], reverse=True)

    # ── 7. Facility pressure (projected bed load per facility) ────────────────
    seen_fac_pbl: set[str] = set()
    facility_pressure: list[dict] = []
    for d in directive_list:
        fid = d["facility_id"]
        if fid in seen_fac_pbl:
            continue
        seen_fac_pbl.add(fid)
        facility_pressure.append({
            "facility_name":                d["facility_name"],
            "facility_id":                  fid,
            "zone_name":                    d["zone_name"],
            "priority_score":               int(d.get("priority_score", 0)),
            "total_beds":                   int(d.get("total_dengue_beds", 0)),
            "projected_bed_load_expected":  round(float(d.get("projected_bed_load_expected", 0)), 1),
            "projected_bed_load_worst":     round(float(d.get("projected_bed_load_worst", 0)), 1),
            "facility_anchor_type":         d.get("facility_anchor_type", ""),
        })
    facility_pressure.sort(
        key=lambda x: x["projected_bed_load_expected"],
        reverse=True,
    )

    # ── 8. Case trend (last 26 available weeks with rainfall overlay) ─────────
    case_trend: list[dict] = []
    if cases_df is not None and len(cases_df) > 0:
        recent = cases_df.tail(26).copy()
        for _, row in recent.iterrows():
            label = f"{int(row['epi_year'])}-W{int(row['epi_week']):02d}"
            rain: float | None = None
            if climate_df is not None:
                match = climate_df[
                    (climate_df["epi_year"] == row["epi_year"]) &
                    (climate_df["epi_week"] == row["epi_week"])
                ]
                if len(match) > 0:
                    rain = round(float(match["rainfall_mm"].iloc[0]), 1)
            case_trend.append({
                "label":       label,
                "cases":       int(row["cases"]),
                "rainfall_mm": rain,
            })

    return {
        "generated_at":        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "actual_vs_predicted": actual_vs_predicted,
        "model_error_bars":    model_error_bars,
        "uncertainty_scenarios": uncertainty_scenarios,
        "zone_priority":       zone_priority,
        "supply_depletion":    supply_depletion,
        "bed_gap":             bed_gap,
        "facility_pressure":   facility_pressure,
        "case_trend":          case_trend,
    }


# ── Validation ────────────────────────────────────────────────────────────────

def validate_outputs() -> list[str]:
    """
    Check that all three output files exist and are well-formed.
    Returns a list of validation error strings (empty = all good).
    """
    errors: list[str] = []

    for path in [DASHBOARD_SUMMARY_PATH, MODEL_COMPARISON_PATH, CHART_DATA_PATH]:
        if not path.exists():
            errors.append(f"Missing output: {path.name}")
            continue
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in {path.name}: {e}")
            continue

        # Spot-check key presence
        if path == DASHBOARD_SUMMARY_PATH:
            for key in ("headline_metrics", "uncertainty", "model_evidence"):
                if key not in data:
                    errors.append(f"{path.name}: missing key '{key}'")
        elif path == MODEL_COMPARISON_PATH:
            if "models" not in data or not data["models"]:
                errors.append(f"{path.name}: 'models' array is empty or missing")
        elif path == CHART_DATA_PATH:
            for key in ("actual_vs_predicted", "zone_priority", "bed_gap"):
                if key not in data or not data[key]:
                    errors.append(f"{path.name}: chart array '{key}' is empty or missing")

    return errors


# ── CLI entry point ───────────────────────────────────────────────────────────

def main() -> None:
    print()
    print("=" * 66)
    print("  DengueOps AI - Phase 6: Dashboard Exporter")
    print("=" * 66)

    # ── Validate required inputs ──────────────────────────────────────────────
    print("\n  Checking required inputs...")
    missing = [p for p in REQUIRED_INPUTS if not p.exists()]
    if missing:
        print("\n  [ERROR] Missing required input files:")
        for p in missing:
            print(f"    - {p}")
        print("\n  Run the full pipeline first:")
        print("    python analytics/run_pipeline.py")
        raise SystemExit(1)
    print("    All required inputs present.")

    # ── Load inputs ───────────────────────────────────────────────────────────
    print("\n  Loading analytics outputs...")
    forecast   = load_json(FORECAST_PATH)
    validation = load_json(VALIDATION_PATH)
    directives = load_json(DIRECTIVES_PATH)
    cases_df   = load_csv_safe(CASES_PATH)
    climate_df = load_csv_safe(CLIMATE_PATH)

    n_directives = len(directives.get("directives", []))
    n_avp        = len(validation.get("actual_vs_predicted", []))
    n_cases      = len(cases_df) if cases_df is not None else 0
    print(f"    Directives: {n_directives}  |  AVP rows: {n_avp}  |  Case rows: {n_cases}")

    # ── Build outputs ─────────────────────────────────────────────────────────
    print("\n  Building dashboard outputs...")

    dashboard_summary = build_dashboard_summary(forecast, validation, directives)
    save_json(DASHBOARD_SUMMARY_PATH, dashboard_summary)
    print(f"    [OK] dashboard_summary.json")

    model_comparison = build_model_comparison(validation)
    save_json(MODEL_COMPARISON_PATH, model_comparison)
    print(f"    [OK] model_comparison.json")

    chart_data = build_chart_data(forecast, validation, directives, cases_df, climate_df)
    save_json(CHART_DATA_PATH, chart_data)
    print(
        f"    [OK] chart_data.json  "
        f"(avp={len(chart_data['actual_vs_predicted'])}  "
        f"zones={len(chart_data['zone_priority'])}  "
        f"sdh={len(chart_data['supply_depletion'])}  "
        f"beds={len(chart_data['bed_gap'])}  "
        f"trend={len(chart_data['case_trend'])})"
    )

    # ── Validate outputs ──────────────────────────────────────────────────────
    print("\n  Validating outputs...")
    errors = validate_outputs()
    if errors:
        print("\n  [WARNING] Validation issues found:")
        for e in errors:
            print(f"    - {e}")
    else:
        print("    All output files valid.")

    # ── Summary ───────────────────────────────────────────────────────────────
    hm = dashboard_summary["headline_metrics"]
    sc = forecast.get("uncertainty_scenarios", {})

    print()
    print(f"  {'-'*62}")
    print(f"  Dashboard Export Complete")
    print(f"    Forecast    : {hm['forecast_cases']} cases | {hm['risk_level']} (score {hm['risk_score']})")
    print(f"    Scenarios   : {sc.get('best_case',{}).get('forecast_cases','?')} / "
          f"{sc.get('expected_case',{}).get('forecast_cases','?')} / "
          f"{sc.get('worst_case',{}).get('forecast_cases','?')} (best/exp/worst)")
    print(f"    Best model  : GradientBoostingRegressor | RMSE {dashboard_summary['model_evidence']['gbr_rmse']}")
    print(f"    Priority zone : {hm['highest_priority_zone']}")
    print(f"    Pressure facility: {hm['highest_pressure_facility'][:50]}")
    print(f"  {'-'*62}")
    print()
    print(f"  Dashboard files ready:")
    print(f"    - {DASHBOARD_SUMMARY_PATH}")
    print(f"    - {MODEL_COMPARISON_PATH}")
    print(f"    - {CHART_DATA_PATH}")
    print()
    print("=" * 66)
    print("  Export complete.")
    print("=" * 66)
    print()


if __name__ == "__main__":
    main()
