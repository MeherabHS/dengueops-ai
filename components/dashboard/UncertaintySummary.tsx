import RiskBadge from "@/components/ui/RiskBadge";
import { SCENARIO_LABELS, SCENARIO_COLORS } from "@/lib/constants";
import type { ForecastOutput } from "@/lib/types";
import { formatNumber, formatGrowthFactor } from "@/lib/formatters";

interface Props {
  forecast: ForecastOutput;
}

export default function UncertaintySummary({ forecast }: Props) {
  const { uncertainty_scenarios } = forecast;

  const rows = [
    { key: "best_case" as const, scenario: uncertainty_scenarios.best_case },
    { key: "expected_case" as const, scenario: uncertainty_scenarios.expected_case },
    { key: "worst_case" as const, scenario: uncertainty_scenarios.worst_case },
  ];

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-100 bg-slate-50">
        <p className="text-sm font-semibold text-slate-700">
          Uncertainty Scenarios — {forecast.horizon_days}-Day Horizon
        </p>
        <p className="text-xs text-slate-400 mt-0.5">
          Approximate ranges derived from model confidence intervals. Not statistically calibrated prediction intervals.
        </p>
      </div>
      <div className="divide-y divide-slate-100">
        {rows.map(({ key, scenario }) => (
          <div key={key} className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-3">
              <div
                className="h-3 w-3 rounded-full flex-shrink-0"
                style={{ backgroundColor: SCENARIO_COLORS[key] }}
              />
              <span className="text-sm font-medium text-slate-700">
                {SCENARIO_LABELS[key]}
              </span>
            </div>
            <div className="flex items-center gap-4 text-right">
              <div>
                <p className="text-xs text-slate-400">Cases</p>
                <p className="text-sm font-bold text-slate-900">
                  {formatNumber(scenario.forecast_cases)}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-400">Growth</p>
                <p className="text-sm font-bold text-slate-900">
                  {formatGrowthFactor(scenario.growth_factor)}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-400">Risk</p>
                <RiskBadge level={scenario.risk_level} size="sm" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
