"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { financialApi } from "@/lib/api";
import { formatINR, formatPercent } from "@/lib/utils";
import { AmortizationChart } from "@/components/amortization-chart";
import { motion } from "framer-motion";
import { HiOutlineBanknotes, HiOutlineCalculator, HiOutlineAdjustmentsHorizontal } from "react-icons/hi2";

export default function LoansPage() {
  const [prepayAmount, setPrepayAmount] = useState(500000);

  const { data: loans } = useQuery({
    queryKey: ["loans"],
    queryFn: async () => {
      try {
        const res = await financialApi.getLoans();
        return res.data;
      } catch {
        return [
          {
            id: "demo-1",
            name: "Home Loan — SBI",
            principal: 3000000,
            outstanding: 2450000,
            annual_rate: 8.5,
            tenure_months: 240,
            remaining_months: 192,
            emi: 26036,
          },
          {
            id: "demo-2",
            name: "Car Loan — HDFC",
            principal: 800000,
            outstanding: 320000,
            annual_rate: 9.2,
            tenure_months: 60,
            remaining_months: 22,
            emi: 16620,
          },
        ];
      }
    },
  });

  // Demo amortization data  
  const amortizationData = Array.from({ length: 20 }, (_, i) => {
    const year = i + 1;
    const totalPayment = 26036 * 12;
    const interestRatio = Math.max(0.1, 1 - (year / 25));
    return {
      year,
      principal: Math.round(totalPayment * (1 - interestRatio)),
      interest: Math.round(totalPayment * interestRatio),
      balance: Math.max(0, Math.round(2450000 * (1 - year / 20))),
    };
  });

  const totalLoans = loans?.length || 0;
  const totalOutstanding = loans?.reduce((s: number, l: { outstanding: number }) => s + l.outstanding, 0) || 0;
  const totalEMI = loans?.reduce((s: number, l: { emi: number }) => s + l.emi, 0) || 0;

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Loans</h1>
          <p className="text-sm text-gray-500 mt-1">Track, analyze, and optimize your debt</p>
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="stat-card">
          <div className="p-2 rounded-lg bg-brand-500/10 w-fit">
            <HiOutlineBanknotes className="w-5 h-5 text-brand-400" />
          </div>
          <p className="stat-value">{formatINR(totalOutstanding)}</p>
          <p className="stat-label">Total Outstanding</p>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="stat-card">
          <div className="p-2 rounded-lg bg-amber-500/10 w-fit">
            <HiOutlineCalculator className="w-5 h-5 text-amber-400" />
          </div>
          <p className="stat-value">{formatINR(totalEMI)}/mo</p>
          <p className="stat-label">Total EMI</p>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="stat-card">
          <div className="p-2 rounded-lg bg-emerald-500/10 w-fit">
            <HiOutlineAdjustmentsHorizontal className="w-5 h-5 text-emerald-400" />
          </div>
          <p className="stat-value">{totalLoans}</p>
          <p className="stat-label">Active Loans</p>
        </motion.div>
      </div>

      {/* Loan cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {loans?.map((loan: { id: string; name: string; principal: number; outstanding: number; annual_rate: number; tenure_months: number; remaining_months: number; emi: number }) => (
          <div key={loan.id} className="glass-card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white">{loan.name}</h3>
              <span className="text-xs font-semibold text-brand-400 bg-brand-500/10 px-2.5 py-1 rounded-full">
                {formatPercent(loan.annual_rate)}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p className="text-xs text-gray-500">Outstanding</p>
                <p className="text-sm font-bold text-white">{formatINR(loan.outstanding)}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Monthly EMI</p>
                <p className="text-sm font-bold text-white">{formatINR(loan.emi)}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Remaining</p>
                <p className="text-sm font-bold text-white">{loan.remaining_months} months</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Original</p>
                <p className="text-sm font-bold text-white">{formatINR(loan.principal)}</p>
              </div>
            </div>

            {/* Progress bar */}
            <div className="mb-2">
              <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                <span>Paid off</span>
                <span>{((1 - loan.outstanding / loan.principal) * 100).toFixed(0)}%</span>
              </div>
              <div className="h-2 bg-surface-700 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${(1 - loan.outstanding / loan.principal) * 100}%` }}
                  transition={{ duration: 1 }}
                  className="h-full bg-gradient-to-r from-brand-500 to-emerald-500 rounded-full"
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Amortization chart */}
      <AmortizationChart data={amortizationData} title="Home Loan Amortization Schedule" />

      {/* Prepayment simulator */}
      <div className="glass-card p-6 mt-6">
        <h3 className="section-title mb-4">Prepayment Simulator</h3>
        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm text-gray-400">Prepayment Amount</label>
              <span className="text-sm font-bold text-brand-400">{formatINR(prepayAmount)}</span>
            </div>
            <input
              id="prepayment-slider"
              type="range"
              min={100000}
              max={2000000}
              step={50000}
              value={prepayAmount}
              onChange={(e) => setPrepayAmount(Number(e.target.value))}
              className="w-full h-2 bg-surface-700 rounded-full appearance-none cursor-pointer
                [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5
                [&::-webkit-slider-thumb]:bg-brand-500 [&::-webkit-slider-thumb]:rounded-full
                [&::-webkit-slider-thumb]:shadow-glow [&::-webkit-slider-thumb]:cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-600 mt-1">
              <span>₹1L</span>
              <span>₹20L</span>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="bg-surface-800/50 rounded-xl p-3 border border-white/[0.04] text-center">
              <p className="text-xs text-gray-500 mb-1">Interest Saved</p>
              <p className="text-sm font-bold text-emerald-400">
                {formatINR(Math.round(prepayAmount * 0.45))}
              </p>
            </div>
            <div className="bg-surface-800/50 rounded-xl p-3 border border-white/[0.04] text-center">
              <p className="text-xs text-gray-500 mb-1">Tenure Reduced</p>
              <p className="text-sm font-bold text-brand-400">
                {Math.round(prepayAmount / 26036)} months
              </p>
            </div>
            <div className="bg-surface-800/50 rounded-xl p-3 border border-white/[0.04] text-center">
              <p className="text-xs text-gray-500 mb-1">New Balance</p>
              <p className="text-sm font-bold text-white">
                {formatINR(Math.max(0, 2450000 - prepayAmount))}
              </p>
            </div>
          </div>
        </div>
        <div className="disclaimer">
          Educational decision support only. Not financial advice.
        </div>
      </div>
    </div>
  );
}
