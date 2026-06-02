"""
spatial_exposure_engine.py
==========================
Phase 0 stub: Allocates city-level forecast cases to operational zones using a
composite spatial exposure index.

Motivation:
    In data-scarce urban settings, ward-level dengue case counts are often unavailable
    or unreliable. A spatial exposure heuristic provides a principled allocation approach
    based on observable zone characteristics.

Exposure Index Composition:
    exposure_index = (
        density_weight * w_density
        + facility_pressure_weight * w_facility
        + mobility_corridor_weight * w_mobility
        + vulnerability_weight * w_vulnerability
    ) * current_anomaly_adjustment

    Where weights w_* are normalised to sum to 1.0 across all zones.

Important limitation:
    This is a heuristic allocation model, NOT a validated spatial epidemiology model.
    No GIS-based spatial analysis is performed in Phase 0.
    Weights are informed by literature and expert judgment, not calibrated to ground truth.

Priority Score:
    priority_score = (exposure_index / risk_score_normalised) * (1 + vulnerability_weight)

Phase 1 replacement:
    Ward-level case counts from DGHS/IEDCR surveillance.
    Validated spatial regression or kriging model.
"""

from __future__ import annotations

from typing import TypedDict


class Zone(TypedDict):
    zone_id: str
    zone_name: str
    density_weight: float
    facility_pressure_weight: float
    mobility_corridor_weight: float
    vulnerability_weight: float
    exposure_index: float
    current_anomaly_adjustment: float


W_DENSITY = 0.35
W_FACILITY = 0.25
W_MOBILITY = 0.20
W_VULNERABILITY = 0.20


def compute_exposure_index(zone: Zone) -> float:
    """Compute composite exposure index for a zone."""
    raw = (
        zone["density_weight"] * W_DENSITY
        + zone["facility_pressure_weight"] * W_FACILITY
        + zone["mobility_corridor_weight"] * W_MOBILITY
        + zone["vulnerability_weight"] * W_VULNERABILITY
    )
    return round(raw * zone["current_anomaly_adjustment"], 4)


def allocate_cases(
    zones: list[Zone], total_forecast_cases: int
) -> dict[str, int]:
    """
    Allocate city-level forecast cases to zones proportional to exposure_index.
    Returns {zone_id: allocated_cases}.
    """
    total_exposure = sum(z["exposure_index"] for z in zones)
    if total_exposure == 0:
        return {z["zone_id"]: 0 for z in zones}

    allocation = {}
    for zone in zones:
        share = zone["exposure_index"] / total_exposure
        allocation[zone["zone_id"]] = round(total_forecast_cases * share)

    return allocation


def compute_priority_score(exposure_index: float, vulnerability_weight: float) -> float:
    """Compute zone priority score."""
    return round(exposure_index * (1 + vulnerability_weight), 4)


if __name__ == "__main__":
    print("[spatial_exposure_engine] Phase 0 stub.")
    print(f"[spatial_exposure_engine] Weights: density={W_DENSITY}, facility={W_FACILITY}, "
          f"mobility={W_MOBILITY}, vulnerability={W_VULNERABILITY}")
