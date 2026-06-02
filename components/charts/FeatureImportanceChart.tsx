"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { FeatureImportanceItem } from "@/lib/types";
import { BRAND } from "@/lib/constants";

interface Props {
  data: FeatureImportanceItem[];
}

export default function FeatureImportanceChart({ data }: Props) {
  const sorted = [...data].sort((a, b) => b.importance - a.importance);

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart
        layout="vertical"
        data={sorted}
        margin={{ top: 5, right: 24, left: 8, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
        <XAxis
          type="number"
          domain={[0, 0.4]}
          tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
          tick={{ fontSize: 11, fill: BRAND.slate }}
        />
        <YAxis
          type="category"
          dataKey="label"
          width={160}
          tick={{ fontSize: 11, fill: BRAND.slate }}
        />
        <Tooltip
          formatter={(v) => [`${(Number(v) * 100).toFixed(1)}%`, "Importance"]}
          contentStyle={{ fontSize: 12 }}
        />
        <Bar dataKey="importance" name="Feature Importance" radius={[0, 4, 4, 0]}>
          {sorted.map((item, i) => (
            <Cell
              key={item.feature}
              fill={i === 0 ? BRAND.navyMid : i === 1 ? BRAND.cyan : BRAND.cyanLight}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
