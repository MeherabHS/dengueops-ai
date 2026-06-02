import { Trophy } from "lucide-react";
import modelComparisonRaw from "@/data/model_comparison.json";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const mc = modelComparisonRaw as any;

const MODEL_META: Record<string, { color: string; badgeColor: string; role: string }> = {
  naive: {
    color: "border-slate-200 bg-slate-50",
    badgeColor: "bg-slate-100 text-slate-600",
    role: "Recent-level continuation baseline",
  },
  moving_average: {
    color: "border-slate-200 bg-slate-50",
    badgeColor: "bg-slate-100 text-slate-600",
    role: "Trend-smoothing baseline",
  },
  gradient_boosting: {
    color: "border-sky-200 bg-sky-50",
    badgeColor: "bg-sky-100 text-sky-700",
    role: "Selected tabular ML model",
  },
};

export default function ModelSummaryCards() {
  const models: {
    model_key: string;
    model_name: string;
    is_selected: boolean;
    mae: number;
    rmse: number;
    mape: number;
  }[] = mc?.models ?? [];

  return (
    <section id="model-cards" className="mb-14">
      <p className="text-xs font-semibold uppercase tracking-wider text-sky-600 mb-2">
        Model Comparison
      </p>
      <h2 className="text-2xl font-bold text-slate-900 mb-2">
        Model Comparison Summary
      </h2>
      <p className="text-sm text-slate-500 max-w-2xl mb-8 leading-relaxed">
        Three models were evaluated on the chronological test period.
        Gradient Boosting Regressor achieved the lowest error metrics across all measures.
      </p>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
        {models.map((m) => {
          const meta = MODEL_META[m.model_key] ?? MODEL_META.naive;
          return (
            <div
              key={m.model_key}
              className={`rounded-xl border ${meta.color} p-5 shadow-sm relative`}
            >
              {m.is_selected && (
                <div className="absolute top-3 right-3">
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 border border-emerald-300 px-2 py-0.5 text-[10px] font-semibold text-emerald-700">
                    <Trophy className="h-3 w-3" /> Selected
                  </span>
                </div>
              )}

              <p className="text-xs font-semibold text-slate-800 mb-0.5 pr-16">{m.model_name}</p>
              <span className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-medium mb-4 ${meta.badgeColor}`}>
                {meta.role}
              </span>

              <div className="grid grid-cols-3 gap-2">
                {[
                  { label: "MAE",      value: m.mae.toFixed(1),    note: "Lower is better" },
                  { label: "RMSE",     value: m.rmse.toFixed(1),   note: "Lower is better" },
                  { label: "MAPE (%)", value: `${m.mape.toFixed(1)}%`, note: "Lower is better" },
                ].map((metric) => (
                  <div key={metric.label} className="text-center rounded-lg bg-white border border-slate-100 py-2.5 px-1">
                    <p className="text-[9px] font-semibold uppercase tracking-wider text-slate-400">
                      {metric.label}
                    </p>
                    <p className={`text-base font-bold mt-0.5 ${
                      m.is_selected ? "text-sky-700" : "text-slate-700"
                    }`}>
                      {metric.value}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* MAE improvement callout */}
      {models.length === 3 && (
        <div className="mt-5 rounded-xl border border-emerald-200 bg-emerald-50 px-5 py-3 flex items-center gap-3">
          <Trophy className="h-4 w-4 text-emerald-600 flex-shrink-0" />
          <p className="text-xs text-emerald-800 leading-relaxed">
            <span className="font-semibold">GBR MAE improvement: </span>
            {Math.round((1 - models[2].mae / models[0].mae) * 100)}% lower MAE than Naive baseline,{" "}
            {Math.round((1 - models[2].mae / models[1].mae) * 100)}% lower MAE than Moving Average baseline.
          </p>
        </div>
      )}
    </section>
  );
}
