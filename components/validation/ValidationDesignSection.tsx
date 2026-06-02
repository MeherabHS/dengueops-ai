import { ArrowRight, AlertTriangle } from "lucide-react";
import validationRaw from "@/data/validation_metrics.json";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const vm = validationRaw as any;

const FLOW_STEPS = [
  { label: "Historical weekly data",      sub: "dengue cases + climate variables" },
  { label: "Lag-aware feature engineering", sub: "14d & 28d lags, rolling stats, seasonality" },
  { label: "Chronological train/test split", sub: `${vm?.train_rows ?? 96} train / ${vm?.test_rows ?? 25} test rows` },
  { label: "Baseline models",             sub: "Naive · Moving Average" },
  { label: "Gradient Boosting model",     sub: "29 engineered features" },
  { label: "Error metrics",               sub: "MAE · RMSE · MAPE" },
  { label: "Forecast uncertainty band",   sub: "RMSE-derived best/expected/worst" },
];

function periodLabel(p: { epi_year_start: number; epi_week_start: number; epi_year_end: number; epi_week_end: number } | undefined) {
  if (!p) return "—";
  return `${p.epi_year_start} W${p.epi_week_start} → ${p.epi_year_end} W${p.epi_week_end}`;
}

export default function ValidationDesignSection() {
  return (
    <section id="design" className="mb-14">
      <p className="text-xs font-semibold uppercase tracking-wider text-sky-600 mb-2">
        Validation Design
      </p>
      <h2 className="text-2xl font-bold text-slate-900 mb-2">Validation Design</h2>
      <p className="text-sm text-slate-500 max-w-2xl mb-8 leading-relaxed">
        The model is evaluated using a time-based holdout — earlier weeks for training,
        later weeks for testing — to reflect realistic deployment conditions where
        future data is never available during inference.
      </p>

      {/* Why NOT random split */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 mb-8">
        <div className="rounded-xl border border-red-200 bg-red-50 p-4">
          <p className="text-xs font-bold text-red-700 mb-2">✗ Random split (not used)</p>
          <ul className="text-xs text-red-600 space-y-1.5 leading-relaxed">
            <li>· Future rows can appear in training set</li>
            <li>· Seasonal outbreak peaks can leak forward</li>
            <li>· Artificially inflates apparent model performance</li>
            <li>· Does not reflect real forecasting conditions</li>
          </ul>
        </div>
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
          <p className="text-xs font-bold text-emerald-700 mb-2">✓ Chronological split (used)</p>
          <ul className="text-xs text-emerald-600 space-y-1.5 leading-relaxed">
            <li>· Train on earlier epi weeks only</li>
            <li>· Test on final {vm?.test_rows ?? 25} epi weeks</li>
            <li>· Every test prediction uses only historical data</li>
            <li>· Simulates real operational forecasting</li>
          </ul>
        </div>
      </div>

      {/* Validation flow */}
      <div className="mb-8">
        <p className="text-sm font-semibold text-slate-700 mb-3">Validation Pipeline Flow</p>
        <div className="flex flex-wrap items-center gap-2 bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          {FLOW_STEPS.map((step, i) => (
            <div key={step.label} className="flex items-center gap-2">
              <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 min-w-[120px]">
                <p className="text-[11px] font-semibold text-slate-800 leading-snug">{step.label}</p>
                <p className="text-[10px] text-slate-400 mt-0.5">{step.sub}</p>
              </div>
              {i < FLOW_STEPS.length - 1 && (
                <ArrowRight className="h-3.5 w-3.5 text-slate-300 flex-shrink-0" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Split metadata */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6 mb-6">
        {[
          { label: "Validation Design",  value: "Chronological 20%" },
          { label: "Train Rows",         value: `${vm?.train_rows ?? 96} weeks` },
          { label: "Test Rows",          value: `${vm?.test_rows ?? 25} weeks` },
          { label: "Forecast Horizon",   value: "14 days (2 epi weeks)" },
          { label: "Train Period",       value: periodLabel(vm?.train_period) },
          { label: "Test Period",        value: periodLabel(vm?.test_period) },
        ].map((m) => (
          <div key={m.label} className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-0.5">{m.label}</p>
            <p className="text-xs font-semibold text-slate-800 leading-snug">{m.value}</p>
          </div>
        ))}
      </div>

      {/* Data mode note */}
      <div className="rounded-xl border border-slate-200 bg-white px-5 py-4 shadow-sm">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 text-xs">
          <div>
            <p className="font-semibold text-slate-500 uppercase tracking-wider text-[10px] mb-1">Target Variable</p>
            <code className="font-mono text-sky-700 bg-sky-50 px-2 py-0.5 rounded text-xs">
              {vm?.target ?? "target_cases_next_2w"}
            </code>
          </div>
          <div>
            <p className="font-semibold text-slate-500 uppercase tracking-wider text-[10px] mb-1">Data Mode</p>
            <span className="rounded-full bg-amber-100 text-amber-700 px-2 py-0.5 text-[10px] font-medium">
              Synthetic / demo aggregate data
            </span>
          </div>
        </div>
      </div>

      <div className="mt-4 flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-5 py-3">
        <AlertTriangle className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" />
        <p className="text-xs text-amber-700 leading-relaxed">
          <span className="font-semibold">Exact note: </span>
          Random row splitting is avoided because it can leak future seasonal and outbreak
          information into the training set. This validation demonstrates pipeline behaviour
          This validation uses controlled synthetic/demo Dhaka South data — weekly dengue cases and climate
          co-variates for 2024–2026 (up to week 24), generated by the DengueOps AI pipeline.
          Optional OpenDengue/NASA POWER integration is available for future real-data validation.
          Spatial allocation is a prototype heuristic —{" "}
          <span className="font-semibold">this is not a deployment-grade epidemiological validation</span>.
        </p>
      </div>
    </section>
  );
}
