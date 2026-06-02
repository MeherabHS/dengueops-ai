// ─── Forecast & Uncertainty ────────────────────────────────────────────────

export type RiskLevel = "Low" | "Moderate" | "High" | "Critical";

export interface UncertaintyScenario {
  forecast_cases: number;
  growth_factor: number;
  risk_score: number;
  risk_level: RiskLevel;
}

export interface ForecastOutput {
  forecast_id: number;
  date_generated: string;
  target_epi_year: number;
  target_epi_week: number;
  horizon_days: number;
  city: string;
  forecast_cases: number;
  growth_factor: number;
  risk_score: number;
  risk_level: RiskLevel;
  model_name: string;
  reference_cases_4w_rolling?: number;
  latest_observed_cases?: number;
  uncertainty_method?: string;
  uncertainty_scenarios: {
    best_case: UncertaintyScenario;
    expected_case: UncertaintyScenario;
    worst_case: UncertaintyScenario;
  };
}

// ─── Validation ────────────────────────────────────────────────────────────

export interface BaselineResult {
  model: string;
  mae: number;
  rmse: number;
  mape: number;
}

export interface ActualVsPredicted {
  epi_week: number;
  actual: number;
  predicted: number;
  lower_bound: number;
  upper_bound: number;
}

export interface SeasonalityDriftPoint {
  year: number;
  peak_week: number;
  peak_cases: number;
}

export interface ValidationMetrics {
  model_name: string;
  test_period: string;
  mae: number;
  rmse: number;
  mape: number;
  r2: number;
  n_test_weeks: number;
  baseline_results: BaselineResult[];
  actual_vs_predicted: ActualVsPredicted[];
  seasonality_drift: SeasonalityDriftPoint[];
  note: string;
}

// ─── Feature Importance ────────────────────────────────────────────────────

export interface FeatureImportanceItem {
  feature: string;
  label: string;
  importance: number;
  lag_weeks: number | null;
  description: string;
}

// ─── Zones ─────────────────────────────────────────────────────────────────

export type ZoneProfile = "High-density informal" | "Dense commercial-residential" | "Mixed residential-institutional" | "High-density transport hub" | "Dense industrial-residential";

export interface Zone {
  zone_id: string;
  zone_name: string;
  city: string;
  population_share: number;
  density_weight: number;
  facility_pressure_weight: number;
  mobility_corridor_weight: number;
  vulnerability_weight: number;
  exposure_index: number;
  current_anomaly_adjustment: number;
  profile: ZoneProfile;
}

// ─── Facilities ────────────────────────────────────────────────────────────

export type FacilityAnchorType = "real_public_hospital_anchor" | "synthetic_local_response_unit";
export type BedCapacitySource = "public_reference_anchor" | "synthetic_demo_assumption";

export interface Facility {
  facility_id: string;
  zone_id: string;
  facility_name: string;
  facility_type: string;
  facility_anchor_type: FacilityAnchorType;
  /** Total general bed count. Public reference for real anchors; synthetic assumption for local units. */
  general_bed_capacity: number;
  /** Synthetic dengue-simulation bed subset — does NOT claim real dengue ward capacity. */
  dengue_bed_capacity_demo: number;
  /** Synthetic demo occupancy figure only. */
  occupied_dengue_beds_demo: number;
  avg_length_of_stay: number;
  /** Synthetic daily throughput used for load-share allocation only. */
  baseline_daily_dengue_cases_demo: number;
  bed_capacity_source: BedCapacitySource;
  readiness_data_status: string;
  inventory_data_status: string;
  notes?: string;
}

// ─── Inventory ─────────────────────────────────────────────────────────────

export type InventoryItem = "NS1/RDT Kit" | "IV Fluid (500ml)";

export interface Inventory {
  inventory_id: string;
  facility_id: string;
  item_name: InventoryItem;
  current_stock: number;
  baseline_daily_consumption: number;
  reorder_threshold_days: number;
}

// ─── Directives ────────────────────────────────────────────────────────────

/** alert_level matches the Python output: "Critical" | "Warning" (capitalised) */
export type AlertLevel = "Critical" | "Warning";

export interface InventoryAlert {
  item_name: string;
  sdh_expected: number;
  threshold_days: number;
  alert_level: AlertLevel;
  message: string;
}

export interface Directive {
  forecast_id: number;
  target_epi_year: number;
  target_epi_week: number;
  // Zone fields
  zone_id: string;
  zone_name: string;
  zone_profile: string;
  // Facility fields
  facility_id: string;
  facility_name: string;
  facility_type: string;
  facility_anchor_type: string;
  data_status: string;
  // Exposure
  exposure_index: number;
  adjusted_exposure: number;
  normalized_exposure: number;
  facility_load_share: number;
  // Facility-level case allocations
  allocated_cases_best: number;
  allocated_cases_expected: number;
  allocated_cases_worst: number;
  // Zone-level case totals (for zone summary tables)
  zone_allocated_cases_best: number;
  zone_allocated_cases_expected: number;
  zone_allocated_cases_worst: number;
  // Priority (zone-level, same for all facilities in zone)
  priority_score: number;
  raw_priority_score: number;
  priority_category: string;
  // Bed load (facility-level)
  projected_bed_load_best: number;
  projected_bed_load_expected: number;
  projected_bed_load_worst: number;
  // Bed gap — POSITIVE value means deficit (0 = no gap)
  bed_gap_best: number;
  bed_gap_expected: number;
  bed_gap_worst: number;
  /** Total general bed count (public reference for real anchors, synthetic for local units) */
  general_bed_capacity: number | null;
  /** Synthetic dengue-simulation bed subset used for bed pressure calculations */
  dengue_bed_capacity_demo: number;
  /** Synthetic demo occupancy figure */
  occupied_dengue_beds_demo: number;
  avg_length_of_stay: number;
  // SDH consumables (null if no inventory for that item type)
  sdh_ns1_best: number | null;
  sdh_ns1_expected: number | null;
  sdh_ns1_worst: number | null;
  sdh_iv_fluid_best: number | null;
  sdh_iv_fluid_expected: number | null;
  sdh_iv_fluid_worst: number | null;
  // Alerts and recommendations
  inventory_alerts: InventoryAlert[];
  recommendations: string[];
  generation_timestamp: string;
}

// ─── Dashboard Summary (from analytics/dashboard_exporter.py) ──────────────

export interface DashboardSummaryHeadlineMetrics {
  forecast_cases: number;
  growth_factor: number;
  risk_level: RiskLevel;
  risk_score: number;
  target_epi_week: number;
  target_epi_year: number;
  highest_priority_zone: string;
  highest_pressure_facility: string;
  critical_supply_alerts: number;
  facilities_with_expected_bed_gap: number;
  total_facilities: number;
  total_public_government_anchors: number;
  critical_priority_zones: number;
}

export interface DashboardSummaryUncertaintyScenario {
  label: string;
  forecast_cases: number;
  growth_factor: number;
  risk_score: number;
  risk_level: RiskLevel;
}

export interface DashboardSummaryUncertaintyMethod {
  type: string;
  source: string;
  model: string;
  rmse: number;
  uncertainty_pct: number;
  note: string;
}

export interface DashboardSummaryUncertainty {
  best_case: DashboardSummaryUncertaintyScenario;
  expected_case: DashboardSummaryUncertaintyScenario;
  worst_case: DashboardSummaryUncertaintyScenario;
  method: DashboardSummaryUncertaintyMethod;
  method_note: string;
}

export interface DashboardSummaryModelEvidence {
  best_model: string;
  best_model_display: string;
  best_model_reason: string;
  validation_design: string;
  train_rows: number;
  test_rows: number;
  gbr_mae: number;
  gbr_rmse: number;
  mae_reduction_vs_naive_pct: number;
  mae_reduction_vs_moving_average_pct: number;
  disclaimer: string;
}

export interface DashboardSummaryOperationalSummary {
  total_recommendations: number;
  critical_priority_zones: number;
  facilities_with_expected_bed_gap: number;
  facilities_with_worst_case_bed_gap: number;
  critical_supply_alerts: number;
  highest_priority_zone: string;
  highest_pressure_facility: string;
}

export interface DashboardSummary {
  project: {
    title: string;
    subtitle: string;
    track: string;
    conference: string;
    mode: string;
    last_updated: string;
    data_status: string;
  };
  headline_metrics: DashboardSummaryHeadlineMetrics;
  uncertainty: DashboardSummaryUncertainty;
  model_evidence: DashboardSummaryModelEvidence;
  operational_summary: DashboardSummaryOperationalSummary;
  ethics_and_assumptions: string[];
}

// ─── Pipeline Run Summary ──────────────────────────────────────────────────

export interface PipelineRunSummary {
  run_timestamp: string;
  status: "success" | "partial" | "failed";
  completed_steps: string[];
  step_timings_sec: Record<string, number>;
  generated_files: string[];
  forecast_summary: {
    forecast_cases: number;
    growth_factor: number;
    risk_level: string;
    risk_score: number;
    target_epi_week: number;
    target_epi_year: number;
    best_case: number;
    expected_case: number;
    worst_case: number;
  };
  directives_summary: {
    total_facilities: number;
    total_public_government_anchors: number;
    critical_priority_zones: number;
    facilities_with_expected_bed_gap: number;
    facilities_with_worst_case_bed_gap: number;
    critical_supply_alerts: number;
    highest_priority_zone: string;
    highest_pressure_facility: string;
    total_recommendations: number;
  };
}

// ─── UI helpers ────────────────────────────────────────────────────────────

export type ScenarioKey = "best_case" | "expected_case" | "worst_case";

export interface NavLink {
  href: string;
  label: string;
}
