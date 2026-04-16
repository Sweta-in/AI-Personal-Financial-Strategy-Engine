"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { formatINR } from "@/lib/utils";
import { motion } from "framer-motion";

interface AmortizationRow {
  year: number;
  principal: number;
  interest: number;
  balance: number;
}

interface AmortizationChartProps {
  data: AmortizationRow[];
  title?: string;
}

export function AmortizationChart({ data, title }: AmortizationChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="glass-card p-6 flex items-center justify-center h-64 text-gray-500">
        No amortization data available
      </div>
    );
  }

  // Aggregate monthly data to yearly if needed
  const chartData = data.map((row) => ({
    year: `Y${row.year}`,
    Principal: Math.round(row.principal),
    Interest: Math.round(row.interest),
    Balance: Math.round(row.balance),
  }));

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="glass-card p-6"
    >
      {title && <h3 className="section-title mb-4">{title}</h3>}

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: 15 }}>
            <defs>
              <linearGradient id="principalGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#6366f1" stopOpacity={0.9} />
                <stop offset="100%" stopColor="#6366f1" stopOpacity={0.6} />
              </linearGradient>
              <linearGradient id="interestGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.9} />
                <stop offset="100%" stopColor="#f59e0b" stopOpacity={0.6} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
            <XAxis
              dataKey="year"
              stroke="#475569"
              fontSize={11}
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
              formatter={(value: number, name: string) => [formatINR(value), name]}
            />

            <Legend
              wrapperStyle={{ fontSize: 12, color: "#94a3b8" }}
              iconType="circle"
              iconSize={8}
            />

            <Bar
              dataKey="Principal"
              stackId="a"
              fill="url(#principalGrad)"
              radius={[0, 0, 0, 0]}
              animationDuration={1000}
            />
            <Bar
              dataKey="Interest"
              stackId="a"
              fill="url(#interestGrad)"
              radius={[4, 4, 0, 0]}
              animationDuration={1200}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Total summary */}
      <div className="grid grid-cols-3 gap-3 mt-4">
        <div className="bg-surface-800/50 rounded-xl p-3 border border-white/[0.04] text-center">
          <p className="text-xs text-gray-500 mb-1">Total Principal</p>
          <p className="text-sm font-bold text-brand-400">
            {formatINR(chartData.reduce((s, r) => s + r.Principal, 0))}
          </p>
        </div>
        <div className="bg-surface-800/50 rounded-xl p-3 border border-white/[0.04] text-center">
          <p className="text-xs text-gray-500 mb-1">Total Interest</p>
          <p className="text-sm font-bold text-amber-400">
            {formatINR(chartData.reduce((s, r) => s + r.Interest, 0))}
          </p>
        </div>
        <div className="bg-surface-800/50 rounded-xl p-3 border border-white/[0.04] text-center">
          <p className="text-xs text-gray-500 mb-1">Final Balance</p>
          <p className="text-sm font-bold text-gray-300">
            {formatINR(chartData[chartData.length - 1]?.Balance || 0)}
          </p>
        </div>
      </div>
    </motion.div>
  );
}
