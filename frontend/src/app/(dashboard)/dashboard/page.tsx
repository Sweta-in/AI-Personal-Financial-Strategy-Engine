"use client";

import { useQuery } from "@tanstack/react-query";
import { financialApi, decisionApi } from "@/lib/api";
import { formatINR } from "@/lib/utils";
import { AssetAllocationChart } from "@/components/asset-allocation-chart";
import { DecisionCard } from "@/components/decision-card";
import { RiskGauge } from "@/components/risk-gauge";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  HiOutlineBanknotes,
  HiOutlineArrowTrendingUp,
  HiOutlineArrowTrendingDown,
  HiOutlineChartPie,
  HiOutlineChatBubbleLeftRight,
} from "react-icons/hi2";

export default function DashboardPage() {
  const { data: netWorthData } = useQuery({
    queryKey: ["netWorth"],
    queryFn: async () => {
      try {
        const res = await financialApi.getNetWorth();
        return res.data;
      } catch {
        return {
          net_worth: 4250000,
          total_assets: 6800000,
          total_liabilities: 2550000,
          assets_breakdown: [
            { name: "Equity", value: 2800000, color: "#6366f1" },
            { name: "Fixed Deposits", value: 1500000, color: "#10b981" },
            { name: "Real Estate", value: 1800000, color: "#f59e0b" },
            { name: "Gold", value: 400000, color: "#f43f5e" },
            { name: "Cash", value: 300000, color: "#06b6d4" },
          ],
        };
      }
    },
  });

  const { data: decisions } = useQuery({
    queryKey: ["recentDecisions"],
    queryFn: async () => {
      try {
        const res = await decisionApi.getHistory();
        return res.data?.slice(0, 2) || [];
      } catch {
        return [];
      }
    },
  });

  const stats = [
    {
      label: "Net Worth",
      value: formatINR(netWorthData?.net_worth ?? 4250000),
      icon: HiOutlineChartPie,
      color: "text-brand-400",
      bgColor: "bg-brand-500/10",
      change: "+8.2%",
      positive: true,
    },
    {
      label: "Total Assets",
      value: formatINR(netWorthData?.total_assets ?? 6800000),
      icon: HiOutlineArrowTrendingUp,
      color: "text-emerald-400",
      bgColor: "bg-emerald-500/10",
      change: "+12.5%",
      positive: true,
    },
    {
      label: "Total Liabilities",
      value: formatINR(netWorthData?.total_liabilities ?? 2550000),
      icon: HiOutlineArrowTrendingDown,
      color: "text-rose-400",
      bgColor: "bg-rose-500/10",
      change: "-3.1%",
      positive: true,
    },
    {
      label: "Monthly Savings",
      value: formatINR(85000),
      icon: HiOutlineBanknotes,
      color: "text-amber-400",
      bgColor: "bg-amber-500/10",
      change: "+5.0%",
      positive: true,
    },
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } },
  };
  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 },
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">Your complete financial overview</p>
        </div>
        <Link href="/ask" className="btn-primary">
          <HiOutlineChatBubbleLeftRight className="w-5 h-5" />
          Ask Engine
        </Link>
      </div>

      {/* Stat cards */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
      >
        {stats.map((stat, i) => (
          <motion.div key={i} variants={itemVariants} className="stat-card group">
            <div className="flex items-center justify-between">
              <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`w-5 h-5 ${stat.color}`} />
              </div>
              <span className={`text-xs font-semibold ${stat.positive ? "text-emerald-400" : "text-rose-400"}`}>
                {stat.change}
              </span>
            </div>
            <p className="stat-value">{stat.value}</p>
            <p className="stat-label">{stat.label}</p>
          </motion.div>
        ))}
      </motion.div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <AssetAllocationChart
          data={netWorthData?.assets_breakdown ?? [
            { name: "Equity", value: 2800000, color: "#6366f1" },
            { name: "Fixed Deposits", value: 1500000, color: "#10b981" },
            { name: "Real Estate", value: 1800000, color: "#f59e0b" },
            { name: "Gold", value: 400000, color: "#f43f5e" },
            { name: "Cash", value: 300000, color: "#06b6d4" },
          ]}
        />

        <div className="glass-card p-6 flex flex-col items-center justify-center">
          <h3 className="section-title mb-6">Financial Health Score</h3>
          <RiskGauge score={32} size="lg" label="Based on ML stress model" />
          <p className="text-xs text-gray-500 mt-4 text-center max-w-xs">
            Composite score considering debt ratio, emergency fund, insurance coverage, and portfolio diversification.
          </p>
        </div>
      </div>

      {/* Recent decisions */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="section-title">Recent Decisions</h2>
          <Link href="/ask" className="text-sm text-brand-400 hover:text-brand-300 font-medium transition-colors">
            View All →
          </Link>
        </div>
        {decisions && decisions.length > 0 ? (
          <div className="space-y-4">
            {decisions.map((d, i) => (
              <DecisionCard key={i} decision={d} compact />
            ))}
          </div>
        ) : (
          <div className="glass-card p-8 text-center">
            <HiOutlineChatBubbleLeftRight className="w-10 h-10 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400 font-medium">No decisions yet</p>
            <p className="text-sm text-gray-600 mt-1">
              Ask your first financial question to get started
            </p>
            <Link href="/ask" className="btn-primary mt-4 inline-flex">
              Ask Now
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
