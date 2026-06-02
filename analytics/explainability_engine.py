"""
explainability_engine.py
========================
Phase 0 stub: Extracts feature importances from the trained GradientBoostingRegressor
and formats them for dashboard display.

Approach:
    sklearn GradientBoostingRegressor exposes feature_importances_ based on
    mean decrease in impurity (MDI) — i.e., gain-based importance.

    Importances are normalised to sum to 1.0 and sorted descending.

Limitation:
    MDI-based importances can be biased toward high-cardinality features.
    Phase 1 may add SHAP values for more reliable instance-level explanations.

Output:
    List of {feature, label, importance, lag_weeks, description} dicts.
    Written to data/placeholder/feature_importance.json.

Phase 1 replacement:
    Will call trained model and compute importances from actual training.
"""

from __future__ import annotations

from typing import Any


FEATURE_METADATA: dict[str, dict] = {
    "cases_lag_1w": {
        "label": "Previous Week Cases",
        "lag_weeks": 1,
        "description": "Dengue case count from the prior epi week — strongest autoregressive signal.",
    },
    "rainfall_lag_4w": {
        "label": "Rainfall (4-Week Lag)",
        "lag_weeks": 4,
        "description": "Cumulative rainfall lagged 4 weeks to align with Aedes mosquito development cycle.",
    },
    "cases_rolling_3w": {
        "label": "Rolling 3-Week Case Mean",
        "lag_weeks": None,
        "description": "3-week rolling average smooths noise and captures short-term trend momentum.",
    },
    "humidity_lag_4w": {
        "label": "Humidity (4-Week Lag)",
        "lag_weeks": 4,
        "description": "Relative humidity lagged 4 weeks; high humidity accelerates larval development.",
    },
    "epi_week_sin": {
        "label": "Epi Week (Seasonal Encoding)",
        "lag_weeks": None,
        "description": "Sine encoding of epi week captures seasonal cyclicity without ordinal bias.",
    },
}


def extract_importances(model: Any, feature_names: list[str]) -> list[dict]:
    """
    Phase 0 stub: Extract feature importances from trained model.
    Phase 1: Will call model.feature_importances_ and normalise.
    """
    print("[explainability_engine] Phase 0 stub — using placeholder importances.")
    return [
        {"feature": k, **v, "importance": imp}
        for (k, v), imp in zip(
            FEATURE_METADATA.items(),
            [0.312, 0.241, 0.198, 0.143, 0.106],
        )
    ]


def format_for_dashboard(importances: list[dict]) -> list[dict]:
    """Sort and clip to top N features for display."""
    return sorted(importances, key=lambda x: x["importance"], reverse=True)[:10]


if __name__ == "__main__":
    print("[explainability_engine] Phase 0 stub.")
    result = extract_importances(None, list(FEATURE_METADATA.keys()))
    for item in result:
        print(f"  {item['label']}: {item['importance']:.3f}")
