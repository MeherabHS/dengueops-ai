import { Info, AlertTriangle } from "lucide-react";
import FormulaCard from "@/components/ui/FormulaCard";
import forecastRaw from "@/data/forecast_output.json";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const fo = forecastRaw as any;
const uc = fo?.uncertainty_scenarios ?? {};

// ─── Risk level rules ───────────────────────────────────────────────────────

const RISK_RULES = [
  { range: "growth_factor < 1.10", level: "Low",      color: "bg-emerald-100 text-emerald-700 border-emerald-300" },
  { range: "1.10 ≤ growth_factor < 1.50", level: "Moderate", color: "bg-yellow-100 text-yellow-700 border-yellow-300" },
  { range: "1.50 ≤ growth_factor < 2.00", level: "High",     color: "bg-orange-100 text-orange-700 border-orange-300" },
  { range: "growth_factor ≥ 2.00", level: "Critical", color: "bg-red-100 text-red-700 border-red-300" },
];

// ─── Priority categories ────────────────────────────────────────────────────

const PRIORITY_CATS = [
  { range: "0 – 25",  label: "Routine",  color: "bg-slate-100 text-slate-700" },
  { range: "26 – 50", label: "Moderate", color: "bg-sky-100 text-sky-700" },
  { range: "51 – 75", label: "High",     color: "bg-orange-100 text-orange-700" },
  { range: "76+",     label: "Critical", color: "bg-red-100 text-red-700" },
];

// ─── Component ──────────────────────────────────────────────────────────────

export default function OperationalLogicSection() {
  return (
    <div className="space-y-14">

      {/* ── 6. Forecasting Layer ──────────────────────────────────────── */}
      <section id="forecasting">
        <p className="text-xs font-semibold uppercase tracking-wider text-sky-600 mb-2">
          Forecasting Layer
        </p>
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Forecasting & Risk Scoring</h2>
        <p className="text-sm text-slate-500 max-w-2xl mb-8 leading-relaxed">
          The GradientBoostingRegressor takes the engineered feature matrix and outputs
          a 14-day ahead case count forecast. The operational engine then derives a growth
          factor, a risk score, and a risk level category.
        </p>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 mb-8">
          <FormulaCard
            title="Growth Factor"
            formula="Growth Factor = Forecast Cases ÷ cases_rolling_4w"
            variables={[
              { symbol: "Forecast Cases",    definition: "ML model 14-day ahead prediction" },
              { symbol: "cases_rolling_4w",  definition: "4-week rolling mean of recent observed cases" },
            ]}
            note="Growth factor > 1.0 indicates surge above recent baseline. Used for risk classification and supply demand adjustment."
          />
          <FormulaCard
            title="Risk Score (0–100)"
            formula="Risk Score = piecewise_linear(growth_factor, thresholds=[1.1, 1.5, 2.0], scores=[0, 50, 75, 100])"
            note="Normalised 0–100 score. Used in priority scoring and headline metric cards. Not a probability estimate."
          />
        </div>

        <div className="mb-8">
          <p className="text-sm font-semibold text-slate-700 mb-3">Risk Level Classification</p>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {RISK_RULES.map((r) => (
              <div key={r.level} className={`rounded-xl border ${r.color} px-4 py-3 text-center`}>
                <p className="text-xs font-bold mb-1">{r.level}</p>
                <p className="text-[10px] font-mono">{r.range}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 7. Uncertainty Scenarios ──────────────────────────────────── */}
      <section id="uncertainty">
        <p className="text-xs font-semibold uppercase tracking-wider text-sky-600 mb-2">
          Uncertainty Engine
        </p>
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Uncertainty Scenarios</h2>
        <p className="text-sm text-slate-500 max-w-2xl mb-8 leading-relaxed">
          Single-point forecasts are insufficient for preparedness planning.
          Three scenarios are generated from validation RMSE to support contingency
          planning under uncertainty.
        </p>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-3 mb-6">
          <FormulaCard
            title="Best Case"
            formula="max(0, Expected Forecast − RMSE)"
            note="Optimistic lower bound. Assumes model performs better than validation RMSE."
          />
          <FormulaCard
            title="Expected Case"
            formula="Model Forecast (point estimate)"
            note="Central estimate from GradientBoostingRegressor."
          />
          <FormulaCard
            title="Worst Case"
            formula="Expected Forecast + RMSE"
            note="Pessimistic upper bound. Assumes model error in the adverse direction."
          />
        </div>

        {/* Current values from forecast_output.json */}
        {uc.best_case && uc.expected_case && uc.worst_case && (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 mb-6">
            {[
              { key: "best_case",     label: "Best Case",     data: uc.best_case,     color: "border-emerald-200 bg-emerald-50" },
              { key: "expected_case", label: "Expected Case", data: uc.expected_case, color: "border-sky-200 bg-sky-50" },
              { key: "worst_case",    label: "Worst Case",    data: uc.worst_case,    color: "border-red-200 bg-red-50" },
            ].map((sc) => (
              <div key={sc.key} className={`rounded-xl border ${sc.color} px-4 py-3`}>
                <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 mb-1">{sc.label}</p>
                <p className="text-2xl font-bold text-slate-900">{sc.data.forecast_cases?.toLocaleString()}</p>
                <p className="text-xs text-slate-500 mt-0.5">
                  GF {sc.data.growth_factor?.toFixed(3)}× · {sc.data.risk_level} · {sc.data.risk_score}/100
                </p>
              </div>
            ))}
          </div>
        )}

        <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-5 py-4">
          <AlertTriangle className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-amber-700 leading-relaxed">
            RMSE-derived uncertainty is used as a prototype planning band, not a statistically
            calibrated confidence interval. The band has unknown coverage probability;
            residuals are not assumed Gaussian. For production use, replace with conformal
            prediction or a bootstrapped ensemble.
          </p>
        </div>
      </section>

      {/* ── 8. Spatial Exposure Allocation ────────────────────────────── */}
      <section id="spatial">
        <p className="text-xs font-semibold uppercase tracking-wider text-sky-600 mb-2">
          Spatial Allocation
        </p>
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Spatial Exposure Allocation</h2>
        <p className="text-sm text-slate-500 max-w-2xl mb-4 leading-relaxed">
          City-level dengue forecasts cannot be directly treated as ward-level forecasts.
          In the absence of validated zone-level case counts — a common constraint in
          data-scarce urban health settings — a transparent spatial exposure heuristic is used.
        </p>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 mb-6">
          <FormulaCard
            title="Exposure Index"
            formula={
              "Exposure Index =\n" +
              "  Population Share     × 0.40\n" +
              "+ Density Weight       × 0.30\n" +
              "+ Facility Pressure    × 0.20\n" +
              "+ Mobility Corridor    × 0.10"
            }
            note="Weights are transparent, domain-informed heuristics — not learned from spatial data."
          />
          <FormulaCard
            title="Zone Case Allocation"
            formula={
              "Adjusted Exposure = Exposure Index\n" +
              "  + Current Anomaly Adjustment\n\n" +
              "Normalized Exposure = Adjusted ÷ Σ Adjusted\n\n" +
              "Allocated Zone Cases = Forecast × Normalized"
            }
            note="Ensures zone case counts sum to city-level forecast. Each zone receives a proportional allocation."
          />
        </div>

        <div className="flex items-start gap-3 rounded-xl border border-sky-200 bg-sky-50 px-5 py-4">
          <Info className="h-4 w-4 text-sky-600 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-sky-800 leading-relaxed">
            This is a spatial disaggregation heuristic under city-level data constraints,
            not a learned ward-level spatial model. Zone-level allocations are{" "}
            <strong>advisory approximations</strong> for preparedness planning,
            not epidemiologically validated zone estimates.
          </p>
        </div>
      </section>

      {/* ── 9. Supply Depletion Horizon ───────────────────────────────── */}
      <section id="sdh">
        <p className="text-xs font-semibold uppercase tracking-wider text-sky-600 mb-2">
          Supply Depletion Horizon
        </p>
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Supply Depletion Horizon (SDH)</h2>
        <p className="text-sm text-slate-500 max-w-2xl mb-8 leading-relaxed">
          SDH estimates how many days a consumable resource may last under forecast-adjusted demand.
          It answers: &ldquo;If surge demand rises by the forecast growth factor, when does stock run out?&rdquo;
        </p>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 mb-6">
          <FormulaCard
            title="Dynamic Daily Demand"
            formula="Dynamic Daily Demand = Baseline Daily Consumption × Forecast Growth Factor"
            variables={[
              { symbol: "Baseline Daily Consumption", definition: "Historical average daily consumption at the facility (synthetic demo value)" },
              { symbol: "Forecast Growth Factor",     definition: "Surge multiplier from forecast engine" },
            ]}
            note="Applied per supply item per facility. Demand rises proportionally with growth factor."
          />
          <FormulaCard
            title="Stock Depletion Horizon (SDH)"
            formula="SDH = Current Stock ÷ Dynamic Daily Demand"
            variables={[
              { symbol: "Current Stock", definition: "Units of supply held at facility (synthetic demo value)" },
            ]}
            note="SDH ≤ 7 days: CRITICAL · SDH ≤ 14 days: WARNING · SDH > 14 days: Adequate"
          />
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3">
            <p className="text-xs font-bold text-emerald-700 mb-1">✓ SDH applies to:</p>
            <ul className="text-xs text-emerald-600 space-y-0.5">
              <li>· NS1/RDT diagnostic kits</li>
              <li>· IV fluids (500 ml)</li>
            </ul>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
            <p className="text-xs font-bold text-slate-600 mb-1">✗ SDH does not apply to:</p>
            <ul className="text-xs text-slate-500 space-y-0.5">
              <li>· Hospital beds (modelled separately via LOS logic)</li>
            </ul>
          </div>
        </div>
      </section>

      {/* ── 10. LOS-Based Bed Pressure ────────────────────────────────── */}
      <section id="bed-pressure">
        <p className="text-xs font-semibold uppercase tracking-wider text-sky-600 mb-2">
          Bed Pressure
        </p>
        <h2 className="text-2xl font-bold text-slate-900 mb-2">LOS-Based Bed Pressure</h2>
        <p className="text-sm text-slate-500 max-w-2xl mb-8 leading-relaxed">
          Hospital beds are not consumables. A patient admitted today occupies a bed for
          their entire length of stay. Projecting bed pressure requires modelling
          concurrent occupancy — not just new admissions per day.
        </p>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 mb-6">
          <FormulaCard
            title="Projected Bed Load"
            formula={
              "Projected Bed Load =\n" +
              "  Occupied Dengue Beds\n" +
              "+ (Allocated Daily Surge Cases × Avg LOS)"
            }
            variables={[
              { symbol: "Occupied Dengue Beds",        definition: "Current dengue bed occupancy (synthetic demo value)" },
              { symbol: "Allocated Daily Surge Cases",  definition: "Zone-allocated new cases per day under forecast" },
              { symbol: "Avg LOS",                      definition: "Average length of dengue inpatient stay (days)" },
            ]}
            note="Models cumulative concurrent bed demand, not a simple daily admission count."
          />
          <FormulaCard
            title="Bed Gap"
            formula="Bed Gap = Projected Bed Load − Demo Dengue Bed Capacity"
            note="Positive bed gap = deficit (beds required exceed available). Bed values are synthetic demo values — not actual clinical capacity claims."
          />
        </div>

        <div className="flex items-start gap-3 rounded-xl border border-sky-200 bg-sky-50 px-5 py-4">
          <Info className="h-4 w-4 text-sky-600 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-sky-800 leading-relaxed">
            All bed capacity values ({`dengue_bed_capacity_demo`}) are synthetic operational
            readiness values used to illustrate the LOS modelling logic.
            Real deployment would require actual facility bed counts, occupancy data,
            and validated average LOS from clinical records.
          </p>
        </div>
      </section>

      {/* ── 11. Vulnerability-Gated Priority Score ────────────────────── */}
      <section id="priority">
        <p className="text-xs font-semibold uppercase tracking-wider text-sky-600 mb-2">
          Priority Scoring
        </p>
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Vulnerability-Gated Priority Score</h2>
        <p className="text-sm text-slate-500 max-w-2xl mb-6 leading-relaxed">
          Simple additive vulnerability scoring would assign permanent high priority to
          high-vulnerability zones even during low-transmission periods — creating misleading
          preparedness signals. The priority score is therefore{" "}
          <span className="font-semibold text-slate-700">vulnerability-gated by forecast risk</span>:
          if forecast risk is zero, priority is zero regardless of vulnerability.
        </p>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 mb-8">
          <FormulaCard
            title="Priority Score"
            formula="Priority Score = Risk Score × (1 + Vulnerability Weight)"
            variables={[
              { symbol: "Risk Score",          definition: "Normalised 0–100 risk score from the forecast engine" },
              { symbol: "Vulnerability Weight", definition: "Zone composite vulnerability index (0–1)" },
            ]}
            note="If Risk Score = 0, Priority Score = 0 regardless of vulnerability. Priority reflects active surge risk, not permanent structural vulnerability."
          />
          <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
            <div className="bg-[#1e3a5f] px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-wider text-sky-300">
                Priority Categories
              </p>
            </div>
            <div className="divide-y divide-slate-100">
              {PRIORITY_CATS.map((cat) => (
                <div key={cat.label} className="flex items-center justify-between px-4 py-3">
                  <span className="text-sm font-mono text-slate-700">{cat.range}</span>
                  <span className={`rounded-full px-3 py-0.5 text-xs font-semibold ${cat.color}`}>
                    {cat.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── 12. Operational Directive Generation ─────────────────────── */}
      <section id="directives">
        <p className="text-xs font-semibold uppercase tracking-wider text-sky-600 mb-2">
          Directive Engine
        </p>
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Operational Directive Generation</h2>
        <p className="text-sm text-slate-500 max-w-2xl mb-8 leading-relaxed">
          The directive engine translates risk and readiness metrics into rule-based,
          tiered preparedness recommendations. Rules are deterministic and transparent —
          there is no hidden learned policy.
        </p>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 mb-8">
          {[
            { cond: "SDH ≤ threshold days",             action: "Reorder supplies (NS1/RDT kits or IV fluids)",     severity: "Critical / Warning" },
            { cond: "Bed gap > 0",                       action: "Activate additional beds / prepare referral protocol", severity: "Warning" },
            { cond: "Priority score ≥ 51 (High/Critical)", action: "Prioritise vector-control response",            severity: "High / Critical" },
            { cond: "Worst-case bed gap > expected gap", action: "Contingency planning for worst-case surge",       severity: "Advisory" },
          ].map((rule) => (
            <div key={rule.cond} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-1">Trigger Condition</p>
              <p className="text-xs font-mono font-semibold text-slate-800 mb-2">{rule.cond}</p>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-1">Directive</p>
              <p className="text-xs text-slate-600 mb-2">{rule.action}</p>
              <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                rule.severity.includes("Critical") ? "bg-red-100 text-red-700" :
                rule.severity.includes("Warning")  ? "bg-orange-100 text-orange-700" :
                "bg-sky-100 text-sky-700"
              }`}>{rule.severity}</span>
            </div>
          ))}
        </div>

        {/* Example directive card */}
        <div>
          <p className="text-sm font-semibold text-slate-700 mb-3">Example Directive Card</p>
          <div className="rounded-xl border border-red-200 bg-red-50 p-5 max-w-lg shadow-sm">
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="text-xs font-bold text-red-700 uppercase tracking-wider">Critical Priority</p>
                <p className="text-sm font-bold text-slate-900 mt-0.5">Kamrangirchar</p>
                <p className="text-xs text-slate-600">Example public anchor facility</p>
              </div>
              <span className="rounded-full bg-red-100 text-red-700 border border-red-300 px-2.5 py-0.5 text-[10px] font-semibold">
                CRITICAL
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs mb-3">
              <div className="rounded bg-white border border-red-100 px-3 py-2">
                <p className="text-[10px] text-slate-400">Expected Bed Gap</p>
                <p className="font-bold text-red-700">12 beds</p>
              </div>
              <div className="rounded bg-white border border-orange-100 px-3 py-2">
                <p className="text-[10px] text-slate-400">NS1 SDH</p>
                <p className="font-bold text-orange-700">7.4 days</p>
              </div>
            </div>
            <div className="space-y-1">
              {[
                "Activate additional beds / prepare referral protocol",
                "Reorder NS1/RDT kits — approaching 7-day threshold",
                "Prioritise vector-control response in zone",
                "Monitor supply levels daily",
              ].map((r) => (
                <div key={r} className="flex items-start gap-2 text-xs text-red-800">
                  <span className="mt-0.5 flex-shrink-0">→</span>
                  {r}
                </div>
              ))}
            </div>
            <p className="mt-3 text-[10px] text-slate-400 italic">
              Advisory output — human review required before any operational action.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
