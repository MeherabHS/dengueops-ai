import { clsx } from "clsx";
import type { ReactNode } from "react";

interface MetricCardProps {
  title: string;
  value: ReactNode;
  subtitle?: string;
  icon?: ReactNode;
  variant?: "default" | "critical" | "warning" | "success" | "info";
  className?: string;
}

const variantStyles = {
  default: "border-slate-200 bg-white",
  critical: "border-red-300 bg-red-50",
  warning: "border-orange-300 bg-orange-50",
  success: "border-emerald-300 bg-emerald-50",
  info: "border-sky-300 bg-sky-50",
};

const titleStyles = {
  default: "text-slate-500",
  critical: "text-red-700",
  warning: "text-orange-700",
  success: "text-emerald-700",
  info: "text-sky-700",
};

export default function MetricCard({
  title,
  value,
  subtitle,
  icon,
  variant = "default",
  className,
}: MetricCardProps) {
  return (
    <div
      className={clsx(
        "rounded-xl border p-4 shadow-sm flex flex-col gap-2",
        variantStyles[variant],
        className
      )}
    >
      <div className="flex items-center justify-between">
        <p className={clsx("text-xs font-semibold uppercase tracking-wider", titleStyles[variant])}>
          {title}
        </p>
        {icon && <span className="text-slate-400">{icon}</span>}
      </div>
      <p className="text-2xl font-bold text-slate-900 leading-tight">{value}</p>
      {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
    </div>
  );
}
