"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { formatINR } from "@/lib/utils";
import { motion } from "framer-motion";

interface MonteCarloData {
  month: number;
  p10: number;
  p50: number;
  p90: number;
}

interface MonteCarloChartProps {
  data: MonteCarloData[];
  title?: string;
}

export function MonteCarloChart({ data, title }: MonteCarloChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="glass-card p-6 flex items-center justify-center h-64 text-gray-500">
        No simulation data available
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="glass-card p-6"
    >
      {title && (
        <h3 className="section-title mb-4">{title}</h3>
      )}

      {/* Legend pills */}
      <div className="flex items-center gap-4 mb-4">
        <LegendPill color="bg-emerald-400" label="P90 (Optimistic)" />
        <LegendPill color="bg-brand-400" label="P50 (Expected)" />
        <LegendPill color="bg-rose-400" label="P10 (Conservative)" />
      </div>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 15 }}>
            <defs>
              <linearGradient id="p90Gradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0.02} />
              </linearGradient>
              <linearGradient id="p50Gradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0.02} />
              </linearGradient>
              <linearGradient id="p10Gradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.02} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />

            <XAxis
              dataKey="month"
              stroke="#475569"
              fontSize={11}
              tickFormatter={(v) => `${v}m`}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              stroke="#475569"
              fontSize={11}
              tickFormatter={(v) => formatINR(v)}
              axisLine={false}
              tickLine={false}
              width={70}
            />

            <Tooltip
              contentStyle={{
                backgroundColor: "rgba(19,23,32,0.95)",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: "12px",
                padding: "12px 16px",
                boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
              }}
              labelStyle={{ color: "#94a3b8", fontSize: 12, marginBottom: 8 }}
              labelFormatter={(v) => `Month ${v}`}
              formatter={(value: unknown, name: unknown) => [
                formatINR(value as number),
                (name as string) === "p90" ? "Optimistic" : (name as string) === "p50" ? "Expected" : "Conservative",
              ]}
            />

            <Area
              type="monotone"
              dataKey="p90"
              stroke="#10b981"
              strokeWidth={2}
              fill="url(#p90Gradient)"
              dot={false}
              animationDuration={1200}
            />
            <Area
              type="monotone"
              dataKey="p50"
              stroke="#6366f1"
              strokeWidth={2.5}
              fill="url(#p50Gradient)"
              dot={false}
              animationDuration={1000}
            />
            <Area
              type="monotone"
              dataKey="p10"
              stroke="#f43f5e"
              strokeWidth={2}
              fill="url(#p10Gradient)"
              dot={false}
              animationDuration={800}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Summary stats */}
      {data.length > 0 && (
        <div className="grid grid-cols-3 gap-3 mt-4">
          <SummaryPill
            label="Conservative"
            value={formatINR(data[data.length - 1].p10)}
            color="text-rose-400"
          />
          <SummaryPill
            label="Expected"
            value={formatINR(data[data.length - 1].p50)}
            color="text-brand-400"
          />
          <SummaryPill
            label="Optimistic"
            value={formatINR(data[data.length - 1].p90)}
            color="text-emerald-400"
          />
        </div>
      )}
    </motion.div>
  );
}

function LegendPill({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <div className={`w-2.5 h-2.5 rounded-full ${color}`} />
      <span className="text-xs text-gray-400">{label}</span>
    </div>
  );
}

function SummaryPill({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="bg-surface-800/50 rounded-xl p-3 border border-white/[0.04] text-center">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-sm font-bold ${color}`}>{value}</p>
    </div>
  );
}
