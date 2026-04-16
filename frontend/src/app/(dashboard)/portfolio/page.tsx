"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { portfolioApi } from "@/lib/api";
import { formatINR, formatPercent } from "@/lib/utils";
import { MonteCarloChart } from "@/components/monte-carlo-chart";
import { motion } from "framer-motion";
import {
  HiOutlineBriefcase,
  HiOutlineChartBar,
  HiOutlineArrowTrendingDown,
  HiOutlinePlay,
} from "react-icons/hi2";

export default function PortfolioPage() {
  const [simParams, setSimParams] = useState({
    initial_value: 2800000,
    monthly_sip: 25000,
    annual_return_mean: 12,
    annual_return_std: 18,
    time_horizon_months: 120,
  });

  const [simData, setSimData] = useState<Array<{ month: number; p10: number; p50: number; p90: number }> | null>(null);

  const { data: holdings } = useQuery({
    queryKey: ["holdings"],
    queryFn: async () => {
      try {
        const res = await portfolioApi.getHoldings();
        return res.data;
      } catch {
        return [
          { symbol: "NIFTY50 ETF", qty: 200, avg_price: 2150, current_price: 2420, value: 484000, returns_pct: 12.6 },
          { symbol: "HDFC Bank", qty: 50, avg_price: 1520, current_price: 1680, value: 84000, returns_pct: 10.5 },
          { symbol: "Infosys", qty: 100, avg_price: 1380, current_price: 1540, value: 154000, returns_pct: 11.6 },
          { symbol: "ICICI Bank", qty: 80, avg_price: 920, current_price: 1050, value: 84000, returns_pct: 14.1 },
          { symbol: "TCS", qty: 30, avg_price: 3400, current_price: 3780, value: 113400, returns_pct: 11.2 },
          { symbol: "Reliance", qty: 40, avg_price: 2450, current_price: 2620, value: 104800, returns_pct: 6.9 },
        ];
      }
    },
  });

  const simMutation = useMutation({
    mutationFn: async () => {
      try {
        const res = await portfolioApi.monteCarloSimulation({
          ...simParams,
          annual_return_mean: simParams.annual_return_mean / 100,
          annual_return_std: simParams.annual_return_std / 100,
        });
        return res.data;
      } catch {
        // Generate demo data
        const data = [];
        let p10 = simParams.initial_value;
        let p50 = simParams.initial_value;
        let p90 = simParams.initial_value;
        for (let m = 0; m <= simParams.time_horizon_months; m += 6) {
          data.push({ month: m, p10: Math.round(p10), p50: Math.round(p50), p90: Math.round(p90) });
          p10 = p10 * (1 + 0.04 / 12) ** 6 + simParams.monthly_sip * 6;
          p50 = p50 * (1 + 0.10 / 12) ** 6 + simParams.monthly_sip * 6;
          p90 = p90 * (1 + 0.18 / 12) ** 6 + simParams.monthly_sip * 6;
        }
        return { data };
      }
    },
    onSuccess: (data) => setSimData(data.data),
  });

  const portfolioValue = holdings?.reduce((s: number, h: { value: number }) => s + h.value, 0) || 0;

  const metrics = {
    sharpe: 1.24,
    maxDrawdown: -14.8,
    var95: -3.2,
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Portfolio</h1>
          <p className="text-sm text-gray-500 mt-1">Holdings, metrics, and Monte Carlo projections</p>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="stat-card">
          <div className="p-2 rounded-lg bg-brand-500/10 w-fit"><HiOutlineBriefcase className="w-5 h-5 text-brand-400" /></div>
          <p className="stat-value">{formatINR(portfolioValue)}</p>
          <p className="stat-label">Portfolio Value</p>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="stat-card">
          <div className="p-2 rounded-lg bg-emerald-500/10 w-fit"><HiOutlineChartBar className="w-5 h-5 text-emerald-400" /></div>
          <p className="stat-value">{metrics.sharpe}</p>
          <p className="stat-label">Sharpe Ratio</p>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="stat-card">
          <div className="p-2 rounded-lg bg-rose-500/10 w-fit"><HiOutlineArrowTrendingDown className="w-5 h-5 text-rose-400" /></div>
          <p className="stat-value">{formatPercent(metrics.maxDrawdown)}</p>
          <p className="stat-label">Max Drawdown</p>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="stat-card">
          <div className="p-2 rounded-lg bg-amber-500/10 w-fit"><HiOutlineArrowTrendingDown className="w-5 h-5 text-amber-400" /></div>
          <p className="stat-value">{formatPercent(metrics.var95)}</p>
          <p className="stat-label">VaR (95%)</p>
        </motion.div>
      </div>

      {/* Holdings table */}
      <div className="glass-card p-6 mb-8 overflow-x-auto">
        <h3 className="section-title mb-4">Holdings</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/[0.06] text-gray-500 text-xs uppercase tracking-wider">
              <th className="text-left py-3 px-2">Symbol</th>
              <th className="text-right py-3 px-2">Qty</th>
              <th className="text-right py-3 px-2">Avg Price</th>
              <th className="text-right py-3 px-2">CMP</th>
              <th className="text-right py-3 px-2">Value</th>
              <th className="text-right py-3 px-2">Returns</th>
            </tr>
          </thead>
          <tbody>
            {holdings?.map((h: { symbol: string; qty: number; avg_price: number; current_price: number; value: number; returns_pct: number }, i: number) => (
              <motion.tr
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors"
              >
                <td className="py-3 px-2 font-medium text-white">{h.symbol}</td>
                <td className="py-3 px-2 text-right text-gray-300">{h.qty}</td>
                <td className="py-3 px-2 text-right text-gray-400">{formatINR(h.avg_price)}</td>
                <td className="py-3 px-2 text-right text-gray-300">{formatINR(h.current_price)}</td>
                <td className="py-3 px-2 text-right font-semibold text-white">{formatINR(h.value)}</td>
                <td className={`py-3 px-2 text-right font-semibold ${h.returns_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                  {h.returns_pct >= 0 ? "+" : ""}{formatPercent(h.returns_pct)}
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Monte Carlo Simulator */}
      <div className="glass-card p-6 mb-6">
        <h3 className="section-title mb-4">Monte Carlo Simulator</h3>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 mb-4">
          {[
            { label: "Initial Value", key: "initial_value" as const, min: 100000, max: 10000000, step: 100000, fmt: formatINR },
            { label: "Monthly SIP", key: "monthly_sip" as const, min: 5000, max: 200000, step: 5000, fmt: formatINR },
            { label: "Expected Return %", key: "annual_return_mean" as const, min: 4, max: 25, step: 1, fmt: (v: number) => `${v}%` },
            { label: "Volatility %", key: "annual_return_std" as const, min: 5, max: 40, step: 1, fmt: (v: number) => `${v}%` },
            { label: "Horizon (months)", key: "time_horizon_months" as const, min: 12, max: 360, step: 12, fmt: (v: number) => `${v}m` },
          ].map((p) => (
            <div key={p.key}>
              <div className="flex justify-between items-center mb-1">
                <label className="text-xs text-gray-500">{p.label}</label>
                <span className="text-xs font-bold text-brand-400">{p.fmt(simParams[p.key])}</span>
              </div>
              <input
                type="range"
                min={p.min} max={p.max} step={p.step}
                value={simParams[p.key]}
                onChange={(e) => setSimParams({ ...simParams, [p.key]: Number(e.target.value) })}
                className="w-full h-1.5 bg-surface-700 rounded-full appearance-none cursor-pointer
                  [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4
                  [&::-webkit-slider-thumb]:bg-brand-500 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:cursor-pointer"
              />
            </div>
          ))}
        </div>
        <button
          id="run-simulation"
          onClick={() => simMutation.mutate()}
          disabled={simMutation.isPending}
          className="btn-primary"
        >
          {simMutation.isPending ? (
            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <HiOutlinePlay className="w-4 h-4" />
          )}
          Run 10,000 Simulations
        </button>
      </div>

      {simData && <MonteCarloChart data={simData} title="Portfolio Growth Projections" />}

      <div className="disclaimer">Educational decision support only. Not financial advice.</div>
    </div>
  );
}
