"use client";

import { useState, useMemo } from "react";
import {
  Activity,
  TrendingUp,
  ShieldCheck,
  MapPin,
  Building2,
  AlertTriangle,
  BedDouble,
  Layers,
  Calendar,
  RefreshCw,
  Database,
  Info,
} from "lucide-react";
import DataModeBanner from "@/components/dashboard/DataModeBanner";
import EthicsBanner from "@/components/dashboard/EthicsBanner";
import AssumptionBanner from "@/components/dashboard/AssumptionBanner";
import DataRefreshStatus from "@/components/dashboard/DataRefreshStatus";
import OperationalWorkflowCard from "@/components/dashboard/OperationalWorkflowCard";
import UserRoleTabs, { type UserRole } from "@/components/dashboard/UserRoleTabs";
import OperationalCommandView from "@/components/dashboard/OperationalCommandView";
import FacilityReadinessView from "@/components/dashboard/FacilityReadinessView";
import PublicAdvisoryPreview from "@/components/dashboard/PublicAdvisoryPreview";
import TechnicalValidationView from "@/components/dashboard/TechnicalValidationView";
import ScenarioSelector from "@/components/dashboard/ScenarioSelector";
import SurgeScenarioSelector from "@/components/dashboard/SurgeScenarioSelector";
import ScenarioExplanationCard from "@/components/dashboard/ScenarioExplanationCard";
import ScenarioImpactPanel from "@/components/dashboard/ScenarioImpactPanel";
import GisHeatmapPreview from "@/components/dashboard/GisHeatmapPreview";
import ScenarioImpactChart from "@/components/charts/ScenarioImpactChart";
import UncertaintySummary from "@/components/dashboard/UncertaintySummary";
import UncertaintyBandChart from "@/components/charts/UncertaintyBandChart";
import MetricCard from "@/components/ui/MetricCard";
import RiskBadge from "@/components/ui/RiskBadge";
import SectionHeader from "@/components/ui/SectionHeader";
import {
  forecastOutput,
  directives,
  dashboardSummary,
} from "@/lib/demo-data";
import type { ScenarioKey } from "@/lib/types";
import { applySurge, getSurgeMeta } from "@/lib/surgeScenarios";
import type { SurgeKey } from "@/lib/surgeScenarios";
import { formatEpiWeek, formatDate, formatNumber, formatGrowthFactor } from "@/lib/formatters";
import { CONFERENCE, ICADHI_TRACK, PROJECT_TITLE, PROJECT_SUBTITLE } from "@/lib/constants";

export default function DashboardPage() {
  const [scenario, setScenario] = useState<ScenarioKey>("expected_case");
  const [role, setRole] = useState<UserRole>("operational");
  const [surgeKey, setSurgeKey] = useState<SurgeKey>("normal");

  const surgeZones = useMemo(() => applySurge(surgeKey), [surgeKey]);
  const surgeMeta  = useMemo(() => getSurgeMeta(surgeKey), [surgeKey]);

  const sc = forecastOutput.uncertainty_scenarios[scenario];
  const hm = dashboardSummary.headline_metrics;
  const op = dashboardSummary.operational_summary;
  const project = dashboardSummary.project;
  const uncertainty = dashboardSummary.uncertainty;

  // Scenario-aware risk variant
  const riskVariant =
    sc.risk_level === "Critical" ? "critical" :
    sc.risk_level === "High"     ? "warning"  :
    sc.risk_level === "Moderate" ? "warning"  : "success";

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-6">

      {/* ──────────────────────────────────────────────────────────────── */}
      {/* 1. TOP HEADER                                                    */}
      {/* ──────────────────────────────────────────────────────────────── */}
      <div className="rounded-2xl border border-[#1e3a5f] bg-gradient-to-br from-[#0f172a] via-[#1e3a5f] to-[#0f172a] px-6 py-5 shadow-lg">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Activity className="h-5 w-5 text-sky-400" />
              <h1 className="text-2xl font-extrabold text-white">{PROJECT_TITLE}</h1>
            </div>
            <p className="text-sm text-sky-300 leading-relaxed max-w-lg">
              {PROJECT_SUBTITLE}
            </p>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2">
              <span className="rounded-full bg-sky-900/60 px-2.5 py-0.5 text-[11px] font-medium text-sky-300 border border-sky-800">
                {CONFERENCE}
              </span>
              <span className="rounded-full bg-sky-900/60 px-2.5 py-0.5 text-[11px] font-medium text-sky-300 border border-sky-800">
                {ICADHI_TRACK}
              </span>
            </div>
          </div>
          <div className="flex flex-col gap-1.5 text-right">
            <div className="flex items-center justify-end gap-1.5 text-xs text-sky-300">
              <Database className="h-3.5 w-3.5" />
              <span>{project.mode}</span>
            </div>
            <div className="flex items-center justify-end gap-1.5 text-xs text-sky-400">
              <RefreshCw className="h-3.5 w-3.5" />
              <span>Updated {formatDate(project.last_updated)}</span>
            </div>
            <div className="flex items-center justify-end gap-1.5 text-xs text-sky-400">
              <Calendar className="h-3.5 w-3.5" />
              <span>
                Target: {formatEpiWeek(forecastOutput.target_epi_year, forecastOutput.target_epi_week)}
              </span>
            </div>
            <p className="text-[10px] text-sky-600 mt-0.5">{project.data_status}</p>
          </div>
        </div>

        {/* Pipeline banner */}
        <div className="mt-4 rounded-lg border border-sky-900/60 bg-[#0f172a]/50 px-4 py-2.5">
          <p className="text-xs text-sky-300 leading-relaxed">
            <span className="font-semibold text-sky-200">Analytics pipeline →</span>{" "}
            Python scripts generate dashboard-ready JSON outputs.
            This dashboard visualizes forecast, validation, uncertainty, resource readiness,
            and operational directives.{" "}
            <span className="text-sky-400">
              Terminal output is not the evaluator-facing product — this dashboard is.
            </span>
          </p>
        </div>
      </div>

      {/* ──────────────────────────────────────────────────────────────── */}
      {/* 2. DATA MODE / ETHICS / ASSUMPTION BANNERS                       */}
      {/* ──────────────────────────────────────────────────────────────── */}
      <DataModeBanner />
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <EthicsBanner />
        <AssumptionBanner />
      </div>
      <DataRefreshStatus />

      {/* ──────────────────────────────────────────────────────────────── */}
      {/* 3. SCENARIO SELECTOR                                             */}
      {/* ──────────────────────────────────────────────────────────────── */}
      <div className="rounded-xl border border-slate-200 bg-white px-5 py-4 shadow-sm">
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
              Forecast Scenario — drives metric cards below
            </p>
            <ScenarioSelector active={scenario} onChange={setScenario} />
          </div>
          <div className="ml-auto hidden sm:flex flex-col items-end gap-0.5">
            <p className="text-xs text-slate-400">
              14-day horizon · {forecastOutput.model_name}
            </p>
            <p className="text-xs text-slate-400">
              Target {forecastOutput.target_epi_year} W{forecastOutput.target_epi_week} ·
              RMSE: {uncertainty.method.rmse} cases
            </p>
          </div>
        </div>
      </div>

      {/* ──────────────────────────────────────────────────────────────── */}
      {/* 4. TOP METRIC CARDS (8 cards — scenario-aware for first 3)       */}
      {/* ──────────────────────────────────────────────────────────────── */}
      <div>
        <SectionHeader
          title="Forecast Overview"
          subtitle="Key preparedness metrics for the selected scenario. Switch scenario above to compare best / expected / worst projections."
        />
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">

          {/* Scenario-aware cards */}
          <MetricCard
            title="Forecasted Cases"
            value={formatNumber(sc.forecast_cases)}
            subtitle={`${
              scenario === "worst_case" ? "Worst" :
              scenario === "best_case"  ? "Best"  : "Expected"
            } case · 14-day ahead`}
            icon={<Activity className="h-4 w-4" />}
            variant={
              scenario === "worst_case" ? "critical" :
              scenario === "expected_case" ? "warning"  : "success"
            }
          />
          <MetricCard
            title="Growth Factor"
            value={formatGrowthFactor(sc.growth_factor)}
            subtitle="vs 4-week rolling average"
            icon={<TrendingUp className="h-4 w-4" />}
            variant={sc.growth_factor >= 2 ? "critical" : sc.growth_factor >= 1.3 ? "warning" : "success"}
          />
          <MetricCard
            title="Risk Level"
            value={<RiskBadge level={sc.risk_level} size="sm" />}
            subtitle={`Risk score: ${sc.risk_score} / 100`}
            variant={riskVariant}
          />
          <MetricCard
            title="Critical Supply Alerts"
            value={hm.critical_supply_alerts.toString()}
            subtitle="Items below 7-day threshold"
            icon={<AlertTriangle className="h-4 w-4" />}
            variant={hm.critical_supply_alerts > 0 ? "critical" : "success"}
          />

          {/* Fixed / operational cards */}
          <MetricCard
            title="Highest Priority Zone"
            value={
              <span className="text-base font-bold leading-tight text-slate-900">
                {hm.highest_priority_zone}
              </span>
            }
            subtitle="Vulnerability-gated exposure priority"
            icon={<MapPin className="h-4 w-4" />}
            variant="info"
          />
          <MetricCard
            title="Highest Pressure Facility"
            value={
              <span className="text-sm font-bold leading-snug text-slate-900">
                {hm.highest_pressure_facility}
              </span>
            }
            subtitle="Largest expected bed deficit"
            icon={<Building2 className="h-4 w-4" />}
            variant="info"
          />
          <MetricCard
            title="Facilities — Bed Gap"
            value={`${op.facilities_with_expected_bed_gap} / ${hm.total_facilities}`}
            subtitle="Expected bed deficit (expected scenario)"
            icon={<BedDouble className="h-4 w-4" />}
            variant={op.facilities_with_expected_bed_gap > 0 ? "warning" : "success"}
          />
          <MetricCard
            title="Facilities Monitored"
            value={hm.total_facilities.toString()}
            subtitle={`${hm.total_public_government_anchors} real public anchors`}
            icon={<ShieldCheck className="h-4 w-4" />}
            variant="default"
          />
        </div>
      </div>

      {/* ──────────────────────────────────────────────────────────────── */}
      {/* 5. FORECAST UNCERTAINTY SECTION                                  */}
      {/* ──────────────────────────────────────────────────────────────── */}
      <div>
        <SectionHeader
          title="Forecast Uncertainty Scenarios — 14-Day Horizon"
          subtitle="Best-case, expected, and worst-case projections derived from RMSE-based validation error."
        />
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          <UncertaintySummary forecast={forecastOutput} />
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-sm font-semibold text-slate-700 mb-3">
              Scenario Case Comparison
            </p>
            <UncertaintyBandChart forecast={forecastOutput} />
          </div>
        </div>

        {/* Method note */}
        <div className="mt-3 flex items-start gap-2 rounded-lg border border-slate-200 bg-slate-50 px-4 py-2.5 text-xs text-slate-500">
          <Info className="h-3.5 w-3.5 flex-shrink-0 mt-0.5 text-slate-400" />
          <p className="leading-relaxed">
            {uncertainty.method_note ??
              "Uncertainty band derived from validation RMSE. Not a calibrated probabilistic interval."}
          </p>
        </div>
      </div>

      {/* ──────────────────────────────────────────────────────────────── */}
      {/* 5b. SURGE SIMULATION SCENARIO SELECTOR + ZONE HEATMAP            */}
      {/* ──────────────────────────────────────────────────────────────── */}
      <div>
        <SectionHeader
          title="Surge Simulation — Scenario Preparedness Preview"
          subtitle="Scenario simulation helps evaluate preparedness sensitivity under different plausible surge patterns. Select a surge scenario to see how zone risk and priorities would shift."
        />

        {/* Selector + disclaimer */}
        <div className="rounded-xl border border-slate-200 bg-white px-5 py-4 shadow-sm mb-5">
          <SurgeScenarioSelector active={surgeKey} onChange={setSurgeKey} />
          <p className="mt-3 text-[10px] text-slate-400 italic">
            Scenario simulation modifies existing dashboard outputs for demonstration. It does not retrain the forecasting model.
          </p>
        </div>

        {/* Explanation + Heatmap side by side */}
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2 mb-5">
          <div className="space-y-4">
            <ScenarioExplanationCard meta={surgeMeta} />
            <ScenarioImpactChart zones={surgeZones} isNormal={surgeKey === "normal"} />
          </div>
          <GisHeatmapPreview zones={surgeZones} surgeKey={surgeKey} />
        </div>

        {/* Zone impact table */}
        <ScenarioImpactPanel
          surgeKey={surgeKey}
          meta={surgeMeta}
          zones={surgeZones}
        />
      </div>

      {/* ──────────────────────────────────────────────────────────────── */}
      {/* 6. OPERATIONAL WORKFLOW (compact)                                */}
      {/* ──────────────────────────────────────────────────────────────── */}
      <OperationalWorkflowCard compact />

      {/* ──────────────────────────────────────────────────────────────── */}
      {/* 7. ROLE SEPARATION ANNOUNCEMENT                                  */}
      {/* ──────────────────────────────────────────────────────────────── */}
      <div className="flex items-start gap-3 rounded-xl border border-[#1e3a5f] bg-[#0f172a] px-5 py-4 shadow-sm">
        <Layers className="h-5 w-5 text-sky-400 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-semibold text-white">
            DengueOps AI separates operational decision outputs from technical model validation.
          </p>
          <p className="mt-1 text-xs text-sky-300 leading-relaxed">
            Public health users see zone-level priorities and translated action recommendations.
            Hospital administrators see facility supply and bed readiness.
            Evaluators and researchers can inspect model evidence, validation metrics,
            and pipeline architecture under the{" "}
            <span className="font-semibold text-sky-200">Technical Validation</span> tab.
          </p>
          <p className="mt-1 text-[10px] text-sky-500">
            Scenario selection above applies to the Operational tab metric cards and uncertainty band.
          </p>
        </div>
      </div>

      {/* ──────────────────────────────────────────────────────────────── */}
      {/* 8. ROLE TABS                                                      */}
      {/* ──────────────────────────────────────────────────────────────── */}
      <UserRoleTabs activeRole={role} onRoleChange={setRole} />

      {/* ──────────────────────────────────────────────────────────────── */}
      {/* 9-13. ROLE CONTENT                                               */}
      {/*   Operational  → Zone Priority + Directives                      */}
      {/*   Facility     → Facility Readiness + SDH + Bed Gap              */}
      {/*   Public       → Public Advisory                                 */}
      {/*   Technical    → Model Evidence + Feature Importance + Pipeline  */}
      {/* ──────────────────────────────────────────────────────────────── */}
      <div className="min-h-[400px]">
        {role === "operational" && (
          <OperationalCommandView
            forecast={forecastOutput}
            directives={directives}
            scenario={scenario}
            onScenarioChange={setScenario}
          />
        )}

        {role === "facility" && (
          <FacilityReadinessView directives={directives} />
        )}

        {role === "public" && (
          <PublicAdvisoryPreview forecast={forecastOutput} />
        )}

        {role === "technical" && (
          <TechnicalValidationView />
        )}
      </div>

      {/* ──────────────────────────────────────────────────────────────── */}
      {/* FOOTER — ethics note                                             */}
      {/* ──────────────────────────────────────────────────────────────── */}
      <div className="rounded-xl border border-slate-200 bg-slate-50 px-5 py-4">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
          Advisory Notice
        </p>
        <ul className="space-y-1 text-xs text-slate-500 list-disc list-inside leading-relaxed">
          {dashboardSummary.ethics_and_assumptions.slice(0, 4).map((note, i) => (
            <li key={i}>{note}</li>
          ))}
        </ul>
        <p className="mt-2 text-[11px] text-slate-400">
          Human review is required before any operational action. Outputs are advisory only.
        </p>
      </div>
    </div>
  );
}
