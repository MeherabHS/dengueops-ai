import { ArrowRight, Info } from "lucide-react";
import forecastRaw from "@/data/forecast_output.json";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const fo = forecastRaw as any;

const method   = fo?.uncertainty_method   ?? {};
const scenarios = fo?.uncertainty_scenarios ?? {};

const RISK_COLORS: Record<string, string> = {
  Low:      "bg-emerald-100 text-emerald-700 border-emerald-200",
  Moderate: "bg-amber-100   text-amber-700   border-amber-200",
  High:     "bg-red-100     text-red-700     border-red-200",
  Critical: "bg-purple-100  text-purple-700  border-purple-200",
};

export default function UncertaintyLinkageSection() {
  const rmse        = method?.rmse          ?? 67.8;
  const baseCase    = scenarios?.expected_case?.forecast_cases ?? 234;
  const bestCase    = scenarios?.best_case  ?? {};
  const expectedCase = scenarios?.expected_case ?? {};
  const worstCase   = scenarios?.worst_case ?? {};

  const scenarioList = [
    { key: "best_case",     data: bestCase,    label: "Best Case",     formula: `max(0, ${baseCase} − ${rmse}) = ${Math.max(0, baseCase - rmse)}` },
    { key: "expected_case", data: expectedCase, label: "Expected Case", formula: `Forecast = ${baseCase}` },
    { key: "worst_case",    data: worstCase,   label: "Worst Case",    formula: `${baseCase} + ${rmse} = ${baseCase + rmse}` },
  ];

  return (
    <section id="uncertainty-linkage" className="mb-14">
      <p className="text-xs font-semibold uppercase tracking-wider text-sky-600 mb-2">
        Uncertainty Linkage
      </p>
      <h2 className="text-2xl font-bold text-slate-900 mb-2">
        Forecast Uncertainty Linkage
      </h2>
      <p className="text-sm text-slate-500 max-w-2xl mb-8 leading-relaxed">
        The validation RMSE is used to build a simple planning band around the forecast.
        This is <strong className="text-slate-700">not a calibrated probabilistic interval</strong>;
        it is a transparent prototype uncertainty band for preparedness planning.
      </p>

      {/* Method summary */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 mb-8">
        {[
          { label: "RMSE Used",          value: `${rmse.toFixed(1)} cases` },
          { label: "Source",             value: "Chronological backtest" },
          { label: "Uncertainty %",      value: `${method?.uncertainty_pct ?? 29}% of forecast` },
          { label: "Interval Type",      value: "RMSE-derived band" },
        ].map((m) => (
          <div key={m.label} className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-0.5">{m.label}</p>
            <p className="text-xs font-bold text-slate-800">{m.value}</p>
          </div>
        ))}
      </div>

      {/* Formula cards */}
      <div className="mb-8">
        <p className="text-sm font-semibold text-slate-700 mb-3">Uncertainty Band Formulas</p>
        <div className="flex flex-wrap items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
          {[
            { name: "Best Case",    formula: "max(0, Forecast − RMSE)",  color: "border-emerald-200 bg-emerald-50 text-emerald-800" },
            { name: "Expected",     formula: "Forecast",                 color: "border-sky-200 bg-sky-50 text-sky-800" },
            { name: "Worst Case",   formula: "Forecast + RMSE",          color: "border-red-200 bg-red-50 text-red-800" },
          ].map((f, i, arr) => (
            <div key={f.name} className="flex items-center gap-3">
              <div className={`rounded-lg border px-4 py-3 font-mono text-xs leading-snug min-w-[160px] ${f.color}`}>
                <p className="text-[10px] font-semibold uppercase tracking-wider mb-1 opacity-70">{f.name}</p>
                <p className="font-semibold">{f.formula}</p>
              </div>
              {i < arr.length - 1 && (
                <ArrowRight className="h-3.5 w-3.5 text-slate-300 flex-shrink-0" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Current scenario output */}
      {Object.keys(scenarios).length > 0 && (
        <div className="mb-8">
          <p className="text-sm font-semibold text-slate-700 mb-3">
            Current Uncertainty Scenarios
            <span className="ml-2 text-[10px] font-normal text-slate-400">from forecast_output.json</span>
          </p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {scenarioList.map((s) => {
              const riskLevel: string = s.data?.risk_level ?? "—";
              const riskColor = RISK_COLORS[riskLevel] ?? "bg-slate-100 text-slate-600 border-slate-200";
              return (
                <div key={s.key} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                  <p className="text-xs font-bold text-slate-700 mb-0.5">{s.label}</p>
                  <p className="text-[10px] font-mono text-slate-400 mb-3">{s.formula}</p>
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Forecast</span>
                      <span className="font-semibold text-slate-800">{s.data?.forecast_cases?.toLocaleString() ?? "—"} cases</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Growth Factor</span>
                      <span className="font-semibold text-slate-800">{s.data?.growth_factor?.toFixed(2) ?? "—"}×</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Risk Level</span>
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold border ${riskColor}`}>
                        {riskLevel}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-5 py-4">
        <Info className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" />
        <p className="text-xs text-amber-700 leading-relaxed">
          <span className="font-semibold">Prototype note: </span>
          {method?.note ??
            "This uncertainty band is derived from validation RMSE and is not a calibrated probabilistic interval. It is designed for transparent preparedness planning under data-scarce conditions."}
        </p>
      </div>
    </section>
  );
}
