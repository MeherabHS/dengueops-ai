"use client";

import { clsx } from "clsx";
import { SCENARIO_LABELS, SCENARIO_COLORS } from "@/lib/constants";
import type { ScenarioKey } from "@/lib/types";

interface Props {
  active: ScenarioKey;
  onChange: (s: ScenarioKey) => void;
}

const SCENARIOS: ScenarioKey[] = ["best_case", "expected_case", "worst_case"];

export default function ScenarioSelector({ active, onChange }: Props) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 mr-1">
        Scenario:
      </span>
      {SCENARIOS.map((key) => (
        <button
          key={key}
          onClick={() => onChange(key)}
          className={clsx(
            "rounded-full px-3 py-1 text-xs font-semibold border transition-all",
            active === key
              ? "text-white shadow-sm"
              : "bg-white text-slate-600 border-slate-200 hover:border-slate-400"
          )}
          style={
            active === key
              ? { backgroundColor: SCENARIO_COLORS[key], borderColor: SCENARIO_COLORS[key] }
              : undefined
          }
        >
          {SCENARIO_LABELS[key]}
        </button>
      ))}
    </div>
  );
}
