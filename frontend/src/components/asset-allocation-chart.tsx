"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { formatINR } from "@/lib/utils";
import { motion } from "framer-motion";

interface AllocationSlice {
  name: string;
  value: number;
  color: string;
}

const DEFAULT_COLORS = [
  "#6366f1", "#10b981", "#f59e0b", "#06b6d4",
  "#8b5cf6", "#f43f5e", "#ec4899", "#14b8a6",
];

interface AssetAllocationChartProps {
  data: AllocationSlice[];
  title?: string;
  totalLabel?: string;
  totalValue?: number;
}

export function AssetAllocationChart({
  data,
  title = "Asset Allocation",
  totalLabel = "Total",
  totalValue,
}: AssetAllocationChartProps) {
  const total = totalValue ?? data.reduce((s, d) => s + d.value, 0);
  const chartData = data.map((d, i) => ({
    ...d,
    color: d.color || DEFAULT_COLORS[i % DEFAULT_COLORS.length],
  }));

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="glass-card p-6"
    >
      {title && <h3 className="section-title mb-4">{title}</h3>}

      <div className="flex items-center gap-6">
        {/* Donut */}
        <div className="relative w-44 h-44 flex-shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={75}
                paddingAngle={3}
                dataKey="value"
                animationDuration={1000}
                stroke="none"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: "rgba(19,23,32,0.95)",
                  border: "1px solid rgba(255,255,255,0.08)",
                  borderRadius: "12px",
                  padding: "8px 12px",
                  boxShadow: "0 4px 16px rgba(0,0,0,0.3)",
                }}
                formatter={(value: number, name: string) => [formatINR(value), name]}
              />
            </PieChart>
          </ResponsiveContainer>
          {/* Center label */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-xs text-gray-500 uppercase">{totalLabel}</span>
            <span className="text-lg font-bold text-white">{formatINR(total)}</span>
          </div>
        </div>

        {/* Legend */}
        <div className="flex-1 space-y-2.5">
          {chartData.map((item, i) => {
            const pct = total > 0 ? ((item.value / total) * 100).toFixed(1) : "0";
            return (
              <div key={i} className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div
                    className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-sm text-gray-300">{item.name}</span>
                </div>
                <div className="text-right">
                  <span className="text-sm font-semibold text-white">{pct}%</span>
                  <span className="text-xs text-gray-500 ml-2">{formatINR(item.value)}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}
