"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { scenarioApi } from "@/lib/api";
import { formatINR, formatPercent, cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import {
  HiOutlineBeaker,
  HiOutlineBriefcase,
  HiOutlineArrowTrendingDown,
  HiOutlineBanknotes,
  HiOutlinePlay,
} from "react-icons/hi2";

type ScenarioType = "job_loss" | "market_crash" | "rate_change";

interface ScenarioResult {
  scenario: string;
  outcome: string;
  metrics: Record<string, string | number>;
  severity: "low" | "medium" | "high";
}

export default function ScenariosPage() {
  const [activeScenario, setActiveScenario] = useState<ScenarioType>("job_loss");
  const [result, setResult] = useState<ScenarioResult | null>(null);

  // Scenario params
  const [jobLoss, setJobLoss] = useState({ monthly_expenses: 60000, emergency_fund: 500000, income_loss_months: 6 });
  const [marketCrash, setMarketCrash] = useState({ portfolio_value: 2800000, drop_percent: 30 });
  const [rateChange, setRateChange] = useState({ loan_outstanding: 2450000, current_rate: 8.5, new_rate: 9.5, remaining_months: 192 });

  const mutation = useMutation({
    mutationFn: async () => {
      try {
        let res;
        if (activeScenario === "job_loss") {
          res = await scenarioApi.jobLossStressTest(jobLoss);
        } else if (activeScenario === "market_crash") {
          res = await scenarioApi.marketCrashTest(marketCrash);
        } else {
          res = await scenarioApi.rateChangeTest(rateChange);
        }
        return res.data;
      } catch {
        // Fallback demo results
        if (activeScenario === "job_loss") {
          const survivalMonths = Math.floor(jobLoss.emergency_fund / jobLoss.monthly_expenses);
          return {
            scenario: "Job Loss Stress Test",
            outcome: survivalMonths >= jobLoss.income_loss_months
              ? `Your emergency fund covers ${survivalMonths} months — you can survive a ${jobLoss.income_loss_months}-month gap.`
              : `Emergency fund covers only ${survivalMonths} months — shortfall of ${jobLoss.income_loss_months - survivalMonths} months.`,
            metrics: {
              "Survival Months": survivalMonths,
              "Monthly Burn": formatINR(jobLoss.monthly_expenses),
              "Fund Remaining": formatINR(Math.max(0, jobLoss.emergency_fund - jobLoss.monthly_expenses * jobLoss.income_loss_months)),
              "Shortfall": formatINR(Math.max(0, jobLoss.monthly_expenses * jobLoss.income_loss_months - jobLoss.emergency_fund)),
            },
            severity: survivalMonths >= jobLoss.income_loss_months ? "low" : survivalMonths >= jobLoss.income_loss_months * 0.5 ? "medium" : "high",
          } as ScenarioResult;
        } else if (activeScenario === "market_crash") {
          const loss = marketCrash.portfolio_value * (marketCrash.drop_percent / 100);
          return {
            scenario: "Market Crash Simulation",
            outcome: `A ${marketCrash.drop_percent}% crash would reduce your portfolio by ${formatINR(loss)} to ${formatINR(marketCrash.portfolio_value - loss)}.`,
            metrics: {
              "Portfolio Before": formatINR(marketCrash.portfolio_value),
              "Portfolio After": formatINR(marketCrash.portfolio_value - loss),
              "Absolute Loss": formatINR(loss),
              "Recovery Time": `${Math.round(marketCrash.drop_percent / 8)} months (est)`,
            },
            severity: marketCrash.drop_percent > 40 ? "high" as const : marketCrash.drop_percent > 20 ? "medium" as const : "low" as const,
          } as ScenarioResult;
        } else {
          const diff = rateChange.new_rate - rateChange.current_rate;
          const emiIncrease = Math.round(rateChange.loan_outstanding * (diff / 100) / 12);
          return {
            scenario: "Interest Rate Change",
            outcome: `A rate change from ${rateChange.current_rate}% to ${rateChange.new_rate}% would change your EMI by ₹${Math.abs(emiIncrease).toLocaleString("en-IN")}/month.`,
            metrics: {
              "Rate Change": `${diff > 0 ? "+" : ""}${diff.toFixed(1)}%`,
              "EMI Impact": `${diff > 0 ? "+" : ""}${formatINR(Math.abs(emiIncrease))}/mo`,
              "Total Extra Cost": formatINR(Math.abs(emiIncrease * rateChange.remaining_months)),
              "Outstanding": formatINR(rateChange.loan_outstanding),
            },
            severity: Math.abs(diff) > 2 ? "high" as const : Math.abs(diff) > 1 ? "medium" as const : "low" as const,
          } as ScenarioResult;
        }
      }
    },
    onSuccess: (data) => setResult(data as ScenarioResult),
  });

  const scenarios = [
    { key: "job_loss" as const, label: "Job Loss", icon: HiOutlineBriefcase, color: "text-amber-400", bg: "bg-amber-500/10" },
    { key: "market_crash" as const, label: "Market Crash", icon: HiOutlineArrowTrendingDown, color: "text-rose-400", bg: "bg-rose-500/10" },
    { key: "rate_change" as const, label: "Rate Change", icon: HiOutlineBanknotes, color: "text-brand-400", bg: "bg-brand-500/10" },
  ];

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">What-If Scenarios</h1>
        <p className="text-sm text-gray-500 mt-1">Stress test your finances against real-world shocks</p>
      </div>

      {/* Scenario tabs */}
      <div className="flex gap-3 mb-6">
        {scenarios.map((s) => (
          <button
            key={s.key}
            id={`scenario-${s.key}`}
            onClick={() => { setActiveScenario(s.key); setResult(null); }}
            className={cn(
              "flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200",
              activeScenario === s.key
                ? `${s.bg} ${s.color} border border-current/20`
                : "bg-surface-800/40 text-gray-500 border border-white/[0.04] hover:text-gray-300"
            )}
          >
            <s.icon className="w-4 h-4" />
            {s.label}
          </button>
        ))}
      </div>

      {/* Scenario controls */}
      <div className="glass-card p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <HiOutlineBeaker className="w-5 h-5 text-brand-400" />
          <h3 className="section-title">Configure Scenario</h3>
        </div>

        <AnimatePresence mode="wait">
          {activeScenario === "job_loss" && (
            <motion.div key="job_loss" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              <SliderControl label="Monthly Expenses" value={jobLoss.monthly_expenses} min={20000} max={200000} step={5000}
                format={formatINR} onChange={(v) => setJobLoss({ ...jobLoss, monthly_expenses: v })} />
              <SliderControl label="Emergency Fund" value={jobLoss.emergency_fund} min={50000} max={3000000} step={50000}
                format={formatINR} onChange={(v) => setJobLoss({ ...jobLoss, emergency_fund: v })} />
              <SliderControl label="Income Loss (months)" value={jobLoss.income_loss_months} min={1} max={24} step={1}
                format={(v) => `${v} mo`} onChange={(v) => setJobLoss({ ...jobLoss, income_loss_months: v })} />
            </motion.div>
          )}
          {activeScenario === "market_crash" && (
            <motion.div key="market_crash" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <SliderControl label="Portfolio Value" value={marketCrash.portfolio_value} min={100000} max={10000000} step={100000}
                format={formatINR} onChange={(v) => setMarketCrash({ ...marketCrash, portfolio_value: v })} />
              <SliderControl label="Market Drop %" value={marketCrash.drop_percent} min={5} max={70} step={5}
                format={(v) => `${v}%`} onChange={(v) => setMarketCrash({ ...marketCrash, drop_percent: v })} />
            </motion.div>
          )}
          {activeScenario === "rate_change" && (
            <motion.div key="rate_change" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="grid grid-cols-1 sm:grid-cols-4 gap-6">
              <SliderControl label="Outstanding" value={rateChange.loan_outstanding} min={500000} max={10000000} step={100000}
                format={formatINR} onChange={(v) => setRateChange({ ...rateChange, loan_outstanding: v })} />
              <SliderControl label="Current Rate %" value={rateChange.current_rate} min={6} max={14} step={0.25}
                format={(v) => `${v}%`} onChange={(v) => setRateChange({ ...rateChange, current_rate: v })} />
              <SliderControl label="New Rate %" value={rateChange.new_rate} min={6} max={14} step={0.25}
                format={(v) => `${v}%`} onChange={(v) => setRateChange({ ...rateChange, new_rate: v })} />
              <SliderControl label="Remaining Months" value={rateChange.remaining_months} min={12} max={360} step={12}
                format={(v) => `${v} mo`} onChange={(v) => setRateChange({ ...rateChange, remaining_months: v })} />
            </motion.div>
          )}
        </AnimatePresence>

        <button
          id="run-scenario"
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
          className="btn-primary mt-6"
        >
          {mutation.isPending ? (
            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <HiOutlinePlay className="w-4 h-4" />
          )}
          Run Stress Test
        </button>
      </div>

      {/* Result */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="glass-card overflow-hidden"
          >
            <div className={cn("h-1", {
              "bg-emerald-500": result.severity === "low",
              "bg-amber-500": result.severity === "medium",
              "bg-rose-500": result.severity === "high",
            })} />
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-white">{result.scenario}</h3>
                <span className={cn("px-3 py-1 rounded-full text-xs font-semibold border", {
                  "bg-emerald-500/10 text-emerald-400 border-emerald-500/20": result.severity === "low",
                  "bg-amber-500/10 text-amber-400 border-amber-500/20": result.severity === "medium",
                  "bg-rose-500/10 text-rose-400 border-rose-500/20": result.severity === "high",
                })}>
                  {result.severity.toUpperCase()} IMPACT
                </span>
              </div>

              <p className="text-sm text-gray-300 mb-6 leading-relaxed">{result.outcome}</p>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {Object.entries(result.metrics).map(([key, val]) => (
                  <div key={key} className="bg-surface-800/50 rounded-xl p-3 border border-white/[0.04]">
                    <p className="text-xs text-gray-500 mb-1">{key}</p>
                    <p className="text-sm font-bold text-white">{String(val)}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="px-6 pb-6">
              <div className="disclaimer">Educational decision support only. Not financial advice.</div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function SliderControl({
  label, value, min, max, step, format, onChange,
}: {
  label: string; value: number; min: number; max: number; step: number;
  format: (v: number) => string; onChange: (v: number) => void;
}) {
  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <label className="text-sm text-gray-400">{label}</label>
        <span className="text-sm font-bold text-brand-400">{format(value)}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-2 bg-surface-700 rounded-full appearance-none cursor-pointer
          [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5
          [&::-webkit-slider-thumb]:bg-brand-500 [&::-webkit-slider-thumb]:rounded-full
          [&::-webkit-slider-thumb]:shadow-glow [&::-webkit-slider-thumb]:cursor-pointer"
      />
    </div>
  );
}
