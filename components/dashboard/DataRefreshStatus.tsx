import { Clock, RefreshCw, Database, UserCog, Users2 } from "lucide-react";
import { forecastOutput } from "@/lib/demo-data";

// ── Helpers ───────────────────────────────────────────────────────────────

function formatDisplayDate(iso: string): string {
  try {
    const d = new Date(iso.endsWith("Z") ? iso : iso + "Z");
    return d.toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "Asia/Dhaka",
    }) + " BST";
  } catch {
    return iso;
  }
}

function computeNextRefresh(iso: string): string {
  try {
    const d = new Date(iso.endsWith("Z") ? iso : iso + "Z");
    d.setDate(d.getDate() + 7);
    d.setHours(9, 0, 0, 0);
    return d.toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "Asia/Dhaka",
    }) + " BST (scheduled)";
  } catch {
    return "+7 days (scheduled)";
  }
}

// ── Status items ──────────────────────────────────────────────────────────

interface StatusItem {
  icon: React.ReactNode;
  label: string;
  value: string;
  valueClass?: string;
}

export default function DataRefreshStatus() {
  const lastRefresh = forecastOutput.date_generated;

  const items: StatusItem[] = [
    {
      icon: <Clock className="h-3.5 w-3.5 text-sky-500" />,
      label: "Last Data Refresh",
      value: formatDisplayDate(lastRefresh),
    },
    {
      icon: <RefreshCw className="h-3.5 w-3.5 text-emerald-500" />,
      label: "Next Scheduled Refresh",
      value: computeNextRefresh(lastRefresh),
      valueClass: "text-emerald-700",
    },
    {
      icon: <Database className="h-3.5 w-3.5 text-slate-400" />,
      label: "Data Mode",
      value: "Synthetic demonstration dataset",
      valueClass: "text-amber-700",
    },
    {
      icon: <UserCog className="h-3.5 w-3.5 text-violet-500" />,
      label: "Pipeline Responsibility",
      value: "MIS Officer / Data Analyst — manages ingestion and scheduled pipeline runs",
    },
    {
      icon: <Users2 className="h-3.5 w-3.5 text-sky-600" />,
      label: "Operational Users",
      value: "Hospital administrators · Public health officials · City Corporation teams — receive translated action alerts only",
    },
  ];

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div className="flex items-center gap-2 bg-slate-50 border-b border-slate-200 px-4 py-2.5">
        <RefreshCw className="h-3.5 w-3.5 text-slate-500" />
        <span className="text-xs font-semibold text-slate-600 uppercase tracking-wide">
          Pipeline & Data Status
        </span>
        <span className="ml-auto inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
          Ready
        </span>
      </div>

      <div className="grid grid-cols-1 divide-y divide-slate-100 sm:grid-cols-2 sm:divide-y-0 sm:divide-x lg:grid-cols-5 lg:divide-x lg:divide-y-0">
        {items.map((item) => (
          <div key={item.label} className="flex flex-col gap-1 px-4 py-3">
            <div className="flex items-center gap-1.5">
              {item.icon}
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                {item.label}
              </span>
            </div>
            <p className={`text-xs font-medium text-slate-700 leading-snug ${item.valueClass ?? ""}`}>
              {item.value}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
