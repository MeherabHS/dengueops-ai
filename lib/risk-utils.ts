import type { RiskLevel } from "./types";
import { RISK_COLORS } from "./constants";

/**
 * Returns the full Tailwind class object for a given risk level.
 */
export function getRiskColor(level: RiskLevel) {
  return RISK_COLORS[level] ?? RISK_COLORS["Low"];
}

/**
 * Returns a variant string used by RiskBadge to pick its visual style.
 */
export function getRiskBadgeVariant(level: RiskLevel): "low" | "moderate" | "high" | "critical" {
  return level.toLowerCase() as "low" | "moderate" | "high" | "critical";
}

/**
 * Classifies a numeric risk score (0–100) into a RiskLevel.
 */
export function classifyRiskLevel(score: number): RiskLevel {
  if (score >= 85) return "Critical";
  if (score >= 65) return "High";
  if (score >= 40) return "Moderate";
  return "Low";
}

/**
 * Formats a priority score to 2 decimal places.
 */
export function formatPriorityScore(score: number): string {
  return score.toFixed(2);
}

/**
 * Returns a hex color string suitable for Recharts given a risk level.
 */
export function getRiskHex(level: RiskLevel): string {
  return RISK_COLORS[level]?.hex ?? "#64748b";
}

/**
 * Determines alert severity based on SDH days remaining.
 */
export function getSdhSeverity(days: number): "ok" | "warning" | "critical" {
  if (days <= 7) return "critical";
  if (days <= 14) return "warning";
  return "ok";
}

/**
 * Returns a human-readable SDH status label.
 */
export function getSdhLabel(days: number): string {
  if (days <= 7) return `${days}d – CRITICAL`;
  if (days <= 14) return `${days}d – WARNING`;
  return `${days}d – Adequate`;
}
