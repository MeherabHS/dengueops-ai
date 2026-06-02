import type { RiskLevel, NavLink, ScenarioKey } from "./types";

export const PROJECT_TITLE = "DengueOps AI";
export const PROJECT_SUBTITLE =
  "Simulation-Based Dengue Surge Preparedness Decision Support for Dhaka South";
export const ICADHI_TRACK = "Track 06: Health Data Analytics & Predictive Systems";
export const CONFERENCE = "IEEE ICADHI 2026";
export const TARGET_CITY = "Dhaka South";

// ─── Risk level palette ────────────────────────────────────────────────────
// Tailwind class strings (bg, text, border)
export const RISK_COLORS: Record<RiskLevel, { bg: string; text: string; border: string; hex: string }> = {
  Low: {
    bg: "bg-emerald-100",
    text: "text-emerald-800",
    border: "border-emerald-300",
    hex: "#10b981",
  },
  Moderate: {
    bg: "bg-yellow-100",
    text: "text-yellow-800",
    border: "border-yellow-300",
    hex: "#f59e0b",
  },
  High: {
    bg: "bg-orange-100",
    text: "text-orange-800",
    border: "border-orange-300",
    hex: "#f97316",
  },
  Critical: {
    bg: "bg-red-100",
    text: "text-red-800",
    border: "border-red-300",
    hex: "#ef4444",
  },
};

// ─── Scenario display ──────────────────────────────────────────────────────
export const SCENARIO_LABELS: Record<ScenarioKey, string> = {
  best_case: "Best Case",
  expected_case: "Expected Case",
  worst_case: "Worst Case",
};

export const SCENARIO_COLORS: Record<ScenarioKey, string> = {
  best_case: "#10b981",
  expected_case: "#0ea5e9",
  worst_case: "#ef4444",
};

// ─── Navigation ───────────────────────────────────────────────────────────
export const NAV_LINKS: NavLink[] = [
  { href: "/", label: "Home" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/methodology", label: "Methodology" },
  { href: "/validation", label: "Validation" },
  { href: "/ethics", label: "Ethics" },
  { href: "/assumptions", label: "Assumptions" },
  { href: "/about", label: "About" },
];

// ─── Chart / brand palette ─────────────────────────────────────────────────
export const BRAND = {
  navy: "#0f172a",
  navyMid: "#1e3a5f",
  cyan: "#0ea5e9",
  cyanLight: "#7dd3fc",
  slate: "#64748b",
  slateLight: "#f1f5f9",
  white: "#ffffff",
  alertRed: "#ef4444",
  alertOrange: "#f97316",
  alertYellow: "#f59e0b",
  success: "#10b981",
};

// ─── SDH thresholds (days) ─────────────────────────────────────────────────
export const SDH_CRITICAL_THRESHOLD = 7;
export const SDH_WARNING_THRESHOLD = 14;

// ─── Bed-gap threshold ─────────────────────────────────────────────────────
export const BED_GAP_WARNING = 0;
