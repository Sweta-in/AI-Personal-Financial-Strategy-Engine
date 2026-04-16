/**
 * Utility functions — formatting, validation, color helpers.
 */

/** Format number as INR currency: ₹12,34,567 */
export function formatINR(value: number): string {
  if (value >= 10000000) {
    return `₹${(value / 10000000).toFixed(2)}Cr`;
  }
  if (value >= 100000) {
    return `₹${(value / 100000).toFixed(2)}L`;
  }
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

/** Format percentage: 8.5% */
export function formatPercent(value: number, decimals = 1): string {
  return `${value.toFixed(decimals)}%`;
}

/** Get color class based on risk score 0-100 */
export function getRiskColor(score: number): string {
  if (score <= 30) return "text-emerald-400";
  if (score <= 60) return "text-amber-400";
  return "text-rose-400";
}

/** Get background color based on risk score */
export function getRiskBgColor(score: number): string {
  if (score <= 30) return "bg-emerald-500";
  if (score <= 60) return "bg-amber-500";
  return "bg-rose-500";
}

/** Get gradient stops for risk gauge */
export function getRiskGradient(score: number): string {
  if (score <= 30) return "from-emerald-500 to-emerald-400";
  if (score <= 60) return "from-amber-500 to-amber-400";
  return "from-rose-500 to-rose-400";
}

/** Category badge colors */
export function getCategoryColor(cat: string): string {
  const m: Record<string, string> = {
    loan_decision: "bg-blue-500/15 text-blue-400 border-blue-500/30",
    portfolio_risk: "bg-violet-500/15 text-violet-400 border-violet-500/30",
    insurance_gap: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
    scenario_planning: "bg-amber-500/15 text-amber-400 border-amber-500/30",
    market_context: "bg-cyan-500/15 text-cyan-400 border-cyan-500/30",
  };
  return m[cat] || "bg-gray-500/15 text-gray-400 border-gray-500/30";
}

/** Clamp value between min and max */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/** Format date string */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** cn — conditional class merge (supports strings, booleans, objects) */
export function cn(
  ...classes: (string | boolean | undefined | null | Record<string, boolean>)[]
): string {
  const result: string[] = [];
  for (const cls of classes) {
    if (!cls) continue;
    if (typeof cls === "string") {
      result.push(cls);
    } else if (typeof cls === "object") {
      for (const [key, val] of Object.entries(cls)) {
        if (val) result.push(key);
      }
    }
  }
  return result.join(" ");
}
