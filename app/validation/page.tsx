import type { Metadata } from "next";
import ValidationHero from "@/components/validation/ValidationHero";
import ValidationDesignSection from "@/components/validation/ValidationDesignSection";
import ModelSummaryCards from "@/components/validation/ModelSummaryCards";
import ModelComparisonTable from "@/components/validation/ModelComparisonTable";
import ActualVsPredictedPanel from "@/components/validation/ActualVsPredictedPanel";
import ErrorComparisonPanel from "@/components/validation/ErrorComparisonPanel";
import UncertaintyLinkageSection from "@/components/validation/UncertaintyLinkageSection";
import ValidationLimitations from "@/components/validation/ValidationLimitations";

export const metadata: Metadata = {
  title: "Validation & Model Evidence — DengueOps AI",
  description:
    "Chronological backtesting, baseline comparison, MAE/RMSE/MAPE model evaluation, actual-vs-predicted analysis, and validation transparency for the DengueOps AI forecasting component.",
};

const JUMP_LINKS = [
  { href: "#design",             label: "Validation Design"    },
  { href: "#model-cards",        label: "Model Cards"          },
  { href: "#comparison-table",   label: "Comparison Table"     },
  { href: "#avp-chart",          label: "Actual vs Predicted"  },
  { href: "#error-chart",        label: "Error Analysis"       },
  { href: "#uncertainty-linkage",label: "Uncertainty Linkage"  },
  { href: "#limitations",        label: "Limitations"          },
  { href: "#proves",             label: "Proves / Doesn't"     },
  { href: "#evaluator-note",     label: "Evaluator Note"       },
];

export default function ValidationPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Navigation bar */}
      <nav className="sticky top-0 z-30 bg-white/95 backdrop-blur border-b border-slate-200 shadow-sm">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-1 overflow-x-auto py-2.5 scrollbar-hide">
            <a
              href="/"
              className="whitespace-nowrap text-[11px] font-semibold text-slate-400 hover:text-slate-700 mr-3 flex-shrink-0"
            >
              ← Home
            </a>
            {JUMP_LINKS.map((l) => (
              <a
                key={l.href}
                href={l.href}
                className="whitespace-nowrap rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] font-medium text-slate-600 hover:bg-sky-50 hover:text-sky-700 hover:border-sky-200 transition-colors flex-shrink-0"
              >
                {l.label}
              </a>
            ))}
            <a
              href="/dashboard"
              className="ml-auto whitespace-nowrap rounded-full bg-[#0f172a] px-4 py-1 text-[11px] font-semibold text-white hover:bg-slate-700 transition-colors flex-shrink-0"
            >
              Dashboard →
            </a>
          </div>
        </div>
      </nav>

      <main className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-10 lg:py-14">

        {/* 1. Hero */}
        <ValidationHero />

        <hr className="border-slate-200 mb-12" />

        {/* 2. Validation Design */}
        <ValidationDesignSection />

        <hr className="border-slate-200 mb-12" />

        {/* 3. Model Comparison Summary Cards */}
        <ModelSummaryCards />

        <hr className="border-slate-200 mb-12" />

        {/* 4. Model Comparison Table + Why Baselines */}
        <ModelComparisonTable />

        <hr className="border-slate-200 mb-12" />

        {/* 5. Actual vs Predicted Chart */}
        <ActualVsPredictedPanel />

        {/* 6. Error Comparison Chart */}
        <ErrorComparisonPanel />

        <hr className="border-slate-200 mb-12" />

        {/* 7. Forecast Uncertainty Linkage */}
        <UncertaintyLinkageSection />

        <hr className="border-slate-200 mb-12" />

        {/* 8. Limitations + Proves/Doesn't + Evaluator Note */}
        <ValidationLimitations />

        {/* Footer spacer */}
        <div className="mt-20 pb-10 flex items-center justify-center">
          <p className="text-[11px] text-slate-400 text-center max-w-lg leading-relaxed">
            DengueOps AI — Simulation-Based Dengue Surge Preparedness Decision Support for Dhaka South.
            &nbsp;Prototype validation only. Not for clinical or official public health decision-making.
          </p>
        </div>
      </main>
    </div>
  );
}
