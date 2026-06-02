import { Activity } from "lucide-react";
import { PROJECT_TITLE, PROJECT_SUBTITLE, ICADHI_TRACK, CONFERENCE } from "@/lib/constants";

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-[#0f172a] text-slate-400">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Activity className="h-5 w-5 text-sky-400" />
              <span className="font-bold text-white">{PROJECT_TITLE}</span>
            </div>
            <p className="text-xs leading-relaxed text-slate-400">{PROJECT_SUBTITLE}</p>
          </div>

          {/* Conference */}
          <div>
            <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Submitted To
            </p>
            <p className="text-sm text-slate-300">{CONFERENCE}</p>
            <p className="text-xs text-slate-400">{ICADHI_TRACK}</p>
          </div>

          {/* Disclaimer */}
          <div>
            <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Disclaimer
            </p>
            <p className="text-xs leading-relaxed text-slate-400">
              Prototype uses aggregated/synthetic data only. No patient-level data is collected
              or processed. This system is advisory; all decisions require qualified public
              health professional review.
            </p>
          </div>
        </div>

        <div className="mt-8 border-t border-slate-700 pt-4 text-center text-xs text-slate-600">
          © {new Date().getFullYear()} DengueOps AI — Phase 0 Scaffold. For research and
          educational demonstration only.
        </div>
      </div>
    </footer>
  );
}
