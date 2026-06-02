import { Trophy, Info } from "lucide-react";
import modelComparisonRaw from "@/data/model_comparison.json";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const mc = modelComparisonRaw as any;

const INTERPRETATIONS: Record<string, string> = {
  naive:
    "Useful minimum benchmark. A model that cannot beat naive last-week repeat provides no operational signal.",
  moving_average:
    "Smooths short-term volatility but may lag behind sudden case increases during outbreak onset.",
  gradient_boosting:
    "Selected: achieved the lowest MAE and RMSE under chronological validation. Uses lag features to capture delayed climate signals.",
};

const WHY_BASELINES = [
  {
    title: "Naive baseline asks:",
    question: "\"What if the current trend simply continues?\"",
    value: "Establishes the minimum bar: if ML model cannot beat this, it adds no value.",
  },
  {
    title: "Moving average asks:",
    question: "\"What if recent average trend is enough?\"",
    value: "Tests whether trend smoothing alone is sufficient — useful when outbreaks are gradual.",
  },
  {
    title: "ML model is useful only if:",
    question: "It improves on both baselines under chronological validation.",
    value: "In this prototype, Gradient Boosting was selected because it performed best on the chronological test period.",
  },
];

export default function ModelComparisonTable() {
  const models: {
    model_key: string;
    model_name: string;
    is_selected: boolean;
    mae: number;
    rmse: number;
    mape: number;
  }[] = mc?.models ?? [];

  return (
    <section id="comparison-table" className="mb-14">
      <p className="text-xs font-semibold uppercase tracking-wider text-sky-600 mb-2">
        Model Selection
      </p>
      <h2 className="text-2xl font-bold text-slate-900 mb-2">
        Model Comparison Table
      </h2>

      <div className="rounded-xl border border-slate-200 overflow-hidden shadow-sm mb-6">
        <table className="min-w-full text-xs">
          <thead className="bg-[#0f172a]">
            <tr>
              {["Model", "Role", "MAE", "RMSE", "MAPE (%)", "Selected?", "Interpretation"].map((h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-left font-semibold text-sky-300 uppercase tracking-wider text-[10px]"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {models.map((m) => (
              <tr key={m.model_key} className={m.is_selected ? "bg-sky-50" : "hover:bg-slate-50"}>
                <td className="px-4 py-3 font-medium text-slate-800 max-w-[160px]">{m.model_name}</td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                    m.is_selected ? "bg-sky-100 text-sky-700" : "bg-slate-100 text-slate-600"
                  }`}>
                    {m.is_selected ? "Primary ML" : "Baseline"}
                  </span>
                </td>
                <td className="px-4 py-3 font-mono text-slate-700">{m.mae.toFixed(1)}</td>
                <td className="px-4 py-3 font-mono text-slate-700">{m.rmse.toFixed(1)}</td>
                <td className="px-4 py-3 font-mono text-slate-700">{m.mape.toFixed(1)}%</td>
                <td className="px-4 py-3 text-center">
                  {m.is_selected ? (
                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
                      <Trophy className="h-3 w-3" /> Yes
                    </span>
                  ) : (
                    <span className="text-slate-300 text-xs">—</span>
                  )}
                </td>
                <td className="px-4 py-3 text-slate-500 text-[11px] leading-relaxed max-w-[220px]">
                  {INTERPRETATIONS[m.model_key] ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Selection rationale */}
      <div className="flex items-start gap-3 rounded-xl border border-sky-200 bg-sky-50 px-5 py-4 mb-8">
        <Info className="h-4 w-4 text-sky-600 flex-shrink-0 mt-0.5" />
        <p className="text-xs text-sky-800 leading-relaxed">
          <span className="font-semibold">Selection rationale: </span>
          GradientBoostingRegressor was selected because it achieved the lowest MAE and RMSE
          under chronological validation. The project does not claim algorithmic novelty;
          the model is used as a practical forecasting component in a decision-support prototype.
        </p>
      </div>

      {/* Why baselines matter */}
      <div>
        <p className="text-sm font-semibold text-slate-700 mb-4">Why Baselines Matter</p>
        <div className="space-y-3">
          {WHY_BASELINES.map((b) => (
            <div key={b.title} className="flex gap-4 rounded-xl border border-slate-200 bg-white px-5 py-4 shadow-sm">
              <div className="flex-1">
                <p className="text-xs font-bold text-slate-800 mb-0.5">{b.title}</p>
                <p className="text-xs text-slate-600 italic mb-1">{b.question}</p>
                <p className="text-xs text-slate-500 leading-relaxed">{b.value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
