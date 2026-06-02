"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { SCENARIO_COLORS, SCENARIO_LABELS } from "@/lib/constants";
import type { ForecastOutput } from "@/lib/types";

interface Props {
  forecast: ForecastOutput;
}

export default function UncertaintyBandChart({ forecast }: Props) {
  const { uncertainty_scenarios } = forecast;

  const data = [
    {
      scenario: SCENARIO_LABELS.best_case,
      cases: uncertainty_scenarios.best_case.forecast_cases,
      risk: uncertainty_scenarios.best_case.risk_score,
      fill: SCENARIO_COLORS.best_case,
    },
    {
      scenario: SCENARIO_LABELS.expected_case,
      cases: uncertainty_scenarios.expected_case.forecast_cases,
      risk: uncertainty_scenarios.expected_case.risk_score,
      fill: SCENARIO_COLORS.expected_case,
    },
    {
      scenario: SCENARIO_LABELS.worst_case,
      cases: uncertainty_scenarios.worst_case.forecast_cases,
      risk: uncertainty_scenarios.worst_case.risk_score,
      fill: SCENARIO_COLORS.worst_case,
    },
  ];

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 5, right: 16, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="scenario" tick={{ fontSize: 11, fill: "#64748b" }} />
        <YAxis tick={{ fontSize: 11, fill: "#64748b" }} />
        <Tooltip
          formatter={(value) => [Number(value).toLocaleString(), "Forecasted Cases"]}
          contentStyle={{ fontSize: 12 }}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="cases" name="Forecasted Cases" radius={[4, 4, 0, 0]}>
          {data.map((entry) => (
            <Cell key={entry.scenario} fill={entry.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
