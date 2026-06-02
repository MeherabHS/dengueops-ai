"""
run_pipeline.py
===============
DengueOps AI — Phase 6: Full Pipeline Runner

One-command orchestrator for the complete DengueOps AI analytics pipeline.
Runs all 7 stages in order, validates expected outputs after each step,
and saves a structured run log.

Usage:
    python analytics/run_pipeline.py
        Run the full pipeline (all 7 steps).

    python analytics/run_pipeline.py --skip-data-generation
        Skip Step 1 (generate_demo_data.py). Use when you do not want to
        overwrite manually-edited CSV/JSON input files.

    python analytics/run_pipeline.py --validate-only
        Check whether all required output files exist and are well-formed.
        Does not run any pipeline steps.

    python analytics/run_pipeline.py --export-dashboard-only
        Run only Step 7 (dashboard_exporter.py) using existing outputs.

Pipeline steps:
    1. generate_demo_data.py   → dengue_cases.csv, climate_data.csv, zones.json,
                                  facilities.json, inventory.json
    2. feature_engineering.py  → model_features.csv
    3. validation_backtest.py  → validation_metrics.json
    4. forecast_model.py       → forecast_output.json
    5. uncertainty_engine.py   → forecast_output.json (updated with scenarios)
    6. operational_engine.py   → directives.json
    7. dashboard_exporter.py   → dashboard_summary.json, model_comparison.json,
                                  chart_data.json

Outputs:
    data/pipeline_run_summary.json  — Structured run log
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT          = Path(__file__).resolve().parent.parent
ANALYTICS_DIR = ROOT / "analytics"
DATA_DIR      = ROOT / "data"
RUN_SUMMARY_PATH = DATA_DIR / "pipeline_run_summary.json"

# ── Pipeline step definitions ─────────────────────────────────────────────────

PIPELINE_STEPS: list[dict] = [
    # Step 1 — Default: controlled synthetic Dhaka South demo data
    # Use --use-opendengue to replace dengue_cases.csv with real Bangladesh data
    # Use --use-nasa-power-climate to replace climate_data.csv with NASA POWER data
    {
        "id":          "generate_demo_data",
        "script":      ANALYTICS_DIR / "generate_demo_data.py",
        "description": "Phase 1 — Generating controlled Dhaka South synthetic/demo data (dengue cases, climate, zones, facilities, inventory)",
        "skippable":   True,   # skipped by --skip-data-generation
        "expected_files": [
            DATA_DIR / "dengue_cases.csv",
            DATA_DIR / "climate_data.csv",
            DATA_DIR / "zones.json",
            DATA_DIR / "facilities.json",
            DATA_DIR / "inventory.json",
        ],
    },
    # ── Analytic steps (always run after data generation) ───────────────────
    {
        "id":          "feature_engineering",
        "script":      ANALYTICS_DIR / "feature_engineering.py",
        "description": "Phase 2 — Building lag-aware feature matrix",
        "skippable":   False,
        "expected_files": [DATA_DIR / "model_features.csv"],
    },
    {
        "id":          "validation_backtest",
        "script":      ANALYTICS_DIR / "validation_backtest.py",
        "description": "Phase 3a — Temporal backtest and model comparison",
        "skippable":   False,
        "expected_files": [DATA_DIR / "validation_metrics.json"],
    },
    {
        "id":          "forecast_model",
        "script":      ANALYTICS_DIR / "forecast_model.py",
        "description": "Phase 3b — Training final model and generating forecast",
        "skippable":   False,
        "expected_files": [DATA_DIR / "forecast_output.json"],
    },
    {
        "id":          "uncertainty_engine",
        "script":      ANALYTICS_DIR / "uncertainty_engine.py",
        "description": "Phase 4 — Applying RMSE-derived uncertainty scenarios",
        "skippable":   False,
        "expected_files": [DATA_DIR / "forecast_output.json"],
        # Extra check: must have uncertainty_scenarios after this step
        "json_checks": {
            DATA_DIR / "forecast_output.json": ["uncertainty_scenarios"],
        },
    },
    {
        "id":          "operational_engine",
        "script":      ANALYTICS_DIR / "operational_engine.py",
        "description": "Phase 5 — Building zone/facility operational directives",
        "skippable":   False,
        "expected_files": [DATA_DIR / "directives.json"],
        "json_checks": {
            DATA_DIR / "directives.json": ["directives", "summary"],
        },
    },
    {
        "id":          "dashboard_exporter",
        "script":      ANALYTICS_DIR / "dashboard_exporter.py",
        "description": "Phase 6 — Exporting dashboard-ready JSON files",
        "skippable":   False,
        "expected_files": [
            DATA_DIR / "dashboard_summary.json",
            DATA_DIR / "model_comparison.json",
            DATA_DIR / "chart_data.json",
        ],
    },
]

# ── Optional real-data steps (injected dynamically, not in default run) ───────
#
# These are experimental/future validation pathways. The default pipeline uses
# controlled synthetic data from generate_demo_data.py which is better suited
# for demonstrating the forecast-to-preparedness workflow.

# OpenDengue real Bangladesh data — replaces dengue_cases.csv
_OPENDENGUE_STEP: dict = {
    "id":          "fetch_opendengue",
    "script":      ANALYTICS_DIR / "fetch_opendengue.py",
    "description": (
        "[Experimental] Phase 0b — Fetching real Bangladesh dengue data from OpenDengue V1.3 "
        "(replaces synthetic dengue_cases.csv)"
    ),
    "skippable":   False,
    "expected_files": [DATA_DIR / "dengue_cases.csv"],
}

# NASA POWER climate step — replaces synthetic climate_data.csv
_NASA_POWER_STEP: dict = {
    "id":          "fetch_nasa_power_climate",
    "script":      ANALYTICS_DIR / "fetch_nasa_power_climate.py",
    "description": (
        "Phase 1b — Fetching NASA POWER climate data for Dhaka South "
        "(replaces synthetic climate_data.csv)"
    ),
    "skippable":   False,
    "expected_files": [DATA_DIR / "climate_data.csv"],
}

# All files that must exist for a fully valid pipeline run
ALL_OUTPUT_FILES: list[Path] = [
    DATA_DIR / "dengue_cases.csv",
    DATA_DIR / "climate_data.csv",
    DATA_DIR / "model_features.csv",
    DATA_DIR / "validation_metrics.json",
    DATA_DIR / "forecast_output.json",
    DATA_DIR / "directives.json",
    DATA_DIR / "dashboard_summary.json",
    DATA_DIR / "model_comparison.json",
    DATA_DIR / "chart_data.json",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _banner(text: str, width: int = 66) -> None:
    print()
    print("=" * width)
    print(f"  {text}")
    print("=" * width)


def _step_header(step_num: int, total: int, description: str) -> None:
    print()
    print(f"  [{step_num}/{total}] {description}")
    print(f"  {'-' * 62}")


def _load_json_safe(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _validate_file(path: Path, json_keys: list[str] | None = None) -> str | None:
    """
    Check a single output file. Returns an error string or None if valid.
    """
    if not path.exists():
        return f"Missing: {path.name}"

    suffix = path.suffix.lower()

    if suffix == ".json":
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return f"Invalid JSON in {path.name}: {e}"
        if json_keys:
            for key in json_keys:
                if key not in data:
                    return f"{path.name}: missing required key '{key}'"

    elif suffix == ".csv":
        try:
            df = pd.read_csv(path, nrows=1)
            if len(df.columns) == 0:
                return f"{path.name}: no columns found"
        except Exception as e:
            return f"Cannot read {path.name}: {e}"

    return None   # valid


def _validate_step_outputs(step: dict) -> list[str]:
    """Validate all expected outputs for a pipeline step."""
    errors: list[str] = []
    for fp in step.get("expected_files", []):
        err = _validate_file(fp)
        if err:
            errors.append(err)

    # Extra JSON key checks
    for fp, keys in step.get("json_checks", {}).items():
        err = _validate_file(fp, json_keys=keys)
        if err:
            errors.append(err)

    return errors


# ── --validate-only ───────────────────────────────────────────────────────────

def cmd_validate_only() -> int:
    """
    Check whether all required output files exist and are well-formed.
    Returns 0 if everything passes, 1 if any check fails.
    """
    _banner("DengueOps AI — Validate Pipeline Outputs")
    print()
    print("  Checking all required output files...\n")

    all_errors: list[str] = []

    checks: list[tuple[Path, list[str] | None]] = [
        (DATA_DIR / "dengue_cases.csv",       None),
        (DATA_DIR / "climate_data.csv",        None),
        (DATA_DIR / "model_features.csv",      None),
        (DATA_DIR / "validation_metrics.json", ["metrics", "best_model", "actual_vs_predicted"]),
        (DATA_DIR / "forecast_output.json",    ["forecast_cases", "uncertainty_scenarios"]),
        (DATA_DIR / "directives.json",         ["directives", "summary"]),
        (DATA_DIR / "dashboard_summary.json",  ["headline_metrics", "uncertainty", "model_evidence"]),
        (DATA_DIR / "model_comparison.json",   ["models", "best_model"]),
        (DATA_DIR / "chart_data.json",         ["actual_vs_predicted", "zone_priority"]),
    ]

    for path, keys in checks:
        err = _validate_file(path, json_keys=keys)
        status = "[PASS]" if err is None else "[FAIL]"
        print(f"    {status}  {path.name}")
        if err:
            print(f"           {err}")
            all_errors.append(err)

    print()
    if all_errors:
        print(f"  {len(all_errors)} check(s) failed.")
        print("  Run: python analytics/run_pipeline.py  to regenerate missing files.")
        return 1
    else:
        print("  All checks passed.")
        return 0


# ── Core pipeline runner ──────────────────────────────────────────────────────

def _insert_after_data_gen(steps: list[dict], step: dict) -> None:
    """
    Inject `step` immediately after all data-generation steps
    (generate_demo_data / fetch_opendengue) so it runs before feature_engineering.
    """
    insert_after = -1
    for i, s in enumerate(steps):
        if s["id"] in ("generate_demo_data", "fetch_opendengue"):
            insert_after = i
    steps.insert(insert_after + 1, step)


def _insert_nasa_step(steps: list[dict]) -> None:
    _insert_after_data_gen(steps, _NASA_POWER_STEP)


def _insert_opendengue_step(steps: list[dict]) -> None:
    # OpenDengue runs BEFORE generate_demo_data so it writes dengue_cases.csv first
    # (generate_demo_data then skips generating it if the file already exists).
    # Insert at position 0 (before data gen step).
    steps.insert(0, _OPENDENGUE_STEP)


def run_step(step: dict, cwd: Path) -> tuple[bool, float]:
    """
    Execute a pipeline step via subprocess.
    Returns (success: bool, elapsed_seconds: float).
    """
    t0 = time.perf_counter()
    result = subprocess.run(
        [sys.executable, str(step["script"])],
        cwd=str(cwd),
    )
    elapsed = time.perf_counter() - t0
    return result.returncode == 0, elapsed


def run_pipeline(
    skip_data_generation: bool = False,
    export_only: bool = False,
    use_nasa_power_climate: bool = False,
    use_opendengue: bool = False,
) -> int:
    """
    Execute the pipeline. Returns 0 on success, 1 on failure.

    Default mode uses controlled synthetic Dhaka South demo data (2024–2026).
    Optional real-data pathways are available via flags but are not the default.

    Args:
        skip_data_generation:   Skip generate_demo_data step.
        export_only:            Run only dashboard_exporter.
        use_nasa_power_climate: [Experimental] Replace synthetic climate_data.csv
                                with real NASA POWER data.
        use_opendengue:         [Experimental] Replace synthetic dengue_cases.csv
                                with real OpenDengue Bangladesh national data.
    """
    _banner("DengueOps AI — Full Analytics Pipeline")

    steps_to_run = PIPELINE_STEPS.copy()

    if export_only:
        steps_to_run = [s for s in PIPELINE_STEPS if s["id"] == "dashboard_exporter"]
        print("\n  Mode: --export-dashboard-only (Step 7 only)")

    elif skip_data_generation:
        steps_to_run = [s for s in PIPELINE_STEPS if not s["skippable"]]
        label = "--skip-data-generation"
        if use_opendengue:
            _insert_opendengue_step(steps_to_run)
            label += " + --use-opendengue [experimental]"
        if use_nasa_power_climate:
            _insert_nasa_step(steps_to_run)
            label += " + --use-nasa-power-climate [experimental]"
        print(f"\n  Mode: {label}")

    else:
        label = "Full pipeline — controlled synthetic demo data (2024–2026)"
        if use_opendengue:
            _insert_opendengue_step(steps_to_run)
            label += " + OpenDengue [experimental]"
        if use_nasa_power_climate:
            _insert_nasa_step(steps_to_run)
            label += " + NASA POWER [experimental]"
        print(f"\n  Mode: {label}")

    total   = len(steps_to_run)
    completed: list[str] = []
    failed:    str | None = None
    timings:   dict[str, float] = {}

    run_start = datetime.now(timezone.utc)

    for idx, step in enumerate(steps_to_run, start=1):
        _step_header(idx, total, step["description"])
        success, elapsed = run_step(step, cwd=ROOT)
        timings[step["id"]] = round(elapsed, 2)

        if not success:
            print(f"\n  [FAILED] {step['id']} exited with non-zero code.")
            print(f"           Script: {step['script']}")
            print("  Pipeline halted. Fix the error above and re-run.")
            failed = step["id"]
            break

        # Validate expected outputs
        errors = _validate_step_outputs(step)
        if errors:
            print(f"\n  [FAILED] Output validation after '{step['id']}':")
            for e in errors:
                print(f"    - {e}")
            failed = step["id"]
            break

        print(f"\n  [OK] {step['id']}  ({elapsed:.1f}s)")
        completed.append(step["id"])

    # ── Save run summary ──────────────────────────────────────────────────────
    status = "success" if failed is None else f"failed_at_{failed}"
    _save_run_summary(run_start, status, completed, timings)

    # ── Final summary ─────────────────────────────────────────────────────────
    if failed is not None:
        return 1

    _print_final_summary()
    return 0


# ── Final summary printer ─────────────────────────────────────────────────────

def _print_final_summary() -> None:
    forecast   = _load_json_safe(DATA_DIR / "forecast_output.json")
    directives = _load_json_safe(DATA_DIR / "directives.json")
    validation = _load_json_safe(DATA_DIR / "validation_metrics.json")

    if not forecast or not directives or not validation:
        print("\n  [WARNING] Could not load output files for final summary.")
        return

    sc = forecast.get("uncertainty_scenarios", {})
    best_c    = sc.get("best_case",     {}).get("forecast_cases", "?")
    exp_c     = sc.get("expected_case", {}).get("forecast_cases", "?")
    worst_c   = sc.get("worst_case",    {}).get("forecast_cases", "?")

    s = directives.get("summary", {})
    m = validation.get("metrics", {}).get("gradient_boosting", {})

    total_w = 66
    print()
    print("=" * total_w)
    print("  DengueOps AI Pipeline Complete")
    print("=" * total_w)
    print(f"  Forecast       : {forecast.get('forecast_cases')} cases"
          f"  |  Risk: {forecast.get('risk_level')} (score {forecast.get('risk_score')})")
    print(f"  Best/Exp/Worst : {best_c} / {exp_c} / {worst_c} cases")
    print(f"  Best model     : GradientBoostingRegressor"
          f"  |  RMSE: {round(float(m.get('rmse', 0)), 1)}"
          f"  |  MAE: {round(float(m.get('mae', 0)), 1)}")
    print(f"  Priority zone  : {s.get('highest_priority_zone', 'N/A')}")
    print(f"  Pressure fac.  : {str(s.get('highest_pressure_facility', 'N/A'))[:50]}")
    print(f"  Critical alerts: {s.get('critical_supply_alerts', 0)}"
          f"  |  Bed gaps: {s.get('facilities_with_expected_bed_gap', 0)} facilities")
    print(f"  Facilities     : {s.get('total_facilities', 0)}"
          f"  ({s.get('total_public_government_anchors', 0)} public/govt anchors)")
    print()
    print("  Dashboard files ready:")
    for fname in ["dashboard_summary.json", "model_comparison.json", "chart_data.json"]:
        print(f"    - data/{fname}")
    print("  Run log:")
    print(f"    - data/pipeline_run_summary.json")
    print("=" * total_w)
    print()


# ── Run summary serializer ────────────────────────────────────────────────────

def _save_run_summary(
    run_start: datetime,
    status: str,
    completed: list[str],
    timings: dict[str, float],
) -> None:
    """Save a structured pipeline run log to data/pipeline_run_summary.json."""
    forecast   = _load_json_safe(DATA_DIR / "forecast_output.json")
    directives = _load_json_safe(DATA_DIR / "directives.json")

    forecast_summary: dict[str, Any] = {}
    if forecast:
        sc = forecast.get("uncertainty_scenarios", {})
        forecast_summary = {
            "forecast_cases":  forecast.get("forecast_cases"),
            "growth_factor":   forecast.get("growth_factor"),
            "risk_level":      forecast.get("risk_level"),
            "risk_score":      forecast.get("risk_score"),
            "target_epi_week": forecast.get("target_epi_week"),
            "target_epi_year": forecast.get("target_epi_year"),
            "best_case":       sc.get("best_case",     {}).get("forecast_cases"),
            "expected_case":   sc.get("expected_case", {}).get("forecast_cases"),
            "worst_case":      sc.get("worst_case",    {}).get("forecast_cases"),
        }

    directives_summary: dict[str, Any] = {}
    if directives:
        directives_summary = directives.get("summary", {})

    generated_files = [str(f) for f in ALL_OUTPUT_FILES if f.exists()]

    dashboard_outputs: dict[str, Any] = {}
    for name in ("dashboard_summary.json", "model_comparison.json", "chart_data.json"):
        p = DATA_DIR / name
        dashboard_outputs[name] = {
            "exists": p.exists(),
            "size_bytes": p.stat().st_size if p.exists() else 0,
        }

    summary = {
        "run_timestamp":       run_start.strftime("%Y-%m-%dT%H:%M:%S"),
        "status":              status,
        "completed_steps":     completed,
        "step_timings_sec":    timings,
        "generated_files":     generated_files,
        "forecast_summary":    forecast_summary,
        "directives_summary":  directives_summary,
        "dashboard_outputs":   dashboard_outputs,
        "notes": [
            "Python pipeline generates dashboard-ready JSON outputs.",
            "Evaluators do not need to inspect terminal outputs.",
            "The Next.js dashboard visualises forecasts, validation metrics, "
            "uncertainty, SDH, bed gaps, and zone/facility directives.",
            "All readiness and inventory values are synthetic demonstration data.",
            "Real facility names are used as public-sector anchor profiles only.",
        ],
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(RUN_SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n  Run log saved: {RUN_SUMMARY_PATH}")


# ── CLI entry point ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="run_pipeline.py",
        description="DengueOps AI — Full Analytics Pipeline Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analytics/run_pipeline.py
      Run the full pipeline with controlled synthetic Dhaka South demo data.
      This is the default demonstration mode.

  python analytics/run_pipeline.py --skip-data-generation
      Skip data generation. Use existing input CSV/JSON files.

  python analytics/run_pipeline.py --validate-only
      Check whether all output files exist and are well-formed.

  python analytics/run_pipeline.py --export-dashboard-only
      Run only the dashboard exporter (Step 7).

  [Experimental real-data pathways — not the default demo]
  python analytics/run_pipeline.py --use-opendengue
      Replace synthetic dengue_cases.csv with OpenDengue Bangladesh national data.

  python analytics/run_pipeline.py --use-nasa-power-climate
      Replace synthetic climate_data.csv with NASA POWER data.

  python analytics/run_pipeline.py --use-opendengue --use-nasa-power-climate
      Use both real data sources (experimental validation pathway).
        """,
    )
    parser.add_argument(
        "--skip-data-generation",
        action="store_true",
        help="Skip fetch_opendengue + generate_demo_data steps. Preserves existing input files.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only check output file existence and validity. No steps are run.",
    )
    parser.add_argument(
        "--export-dashboard-only",
        action="store_true",
        help="Only run dashboard_exporter.py (Step 7).",
    )
    parser.add_argument(
        "--use-nasa-power-climate",
        action="store_true",
        help=(
            "[Experimental] Fetch NASA POWER climate data for Dhaka South and use it as "
            "climate_data.csv (replaces synthetic climate). Uses cached raw file if available."
        ),
    )
    parser.add_argument(
        "--use-opendengue",
        action="store_true",
        help=(
            "[Experimental] Fetch real Bangladesh national dengue data from OpenDengue V1.3 "
            "(Clarke et al. 2024) and use it as dengue_cases.csv (replaces synthetic cases). "
            "Note: real data covers 2014–2024 (national level). The default synthetic dataset "
            "is better suited for the preparedness workflow demonstration."
        ),
    )

    args = parser.parse_args()

    if args.validate_only:
        sys.exit(cmd_validate_only())
    elif args.export_dashboard_only:
        sys.exit(run_pipeline(export_only=True))
    else:
        sys.exit(run_pipeline(
            skip_data_generation=args.skip_data_generation,
            use_nasa_power_climate=args.use_nasa_power_climate,
            use_opendengue=args.use_opendengue,
        ))


if __name__ == "__main__":
    main()
