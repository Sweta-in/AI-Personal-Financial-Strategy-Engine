"use client";

import { DecisionResponse } from "@/lib/api";
import { formatINR, getRiskColor, getRiskGradient, getCategoryColor, formatDate, cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { HiOutlineSparkles, HiOutlineExclamationTriangle } from "react-icons/hi2";

interface DecisionCardProps {
  decision: DecisionResponse;
  compact?: boolean;
}

export function DecisionCard({ decision, compact = false }: DecisionCardProps) {
  const { recommendation, quantitative_summary, risk_score, question_type, disclaimer } = decision;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="glass-card overflow-hidden"
    >
      {/* Header gradient bar */}
      <div className="h-1 bg-gradient-to-r from-brand-500 via-brand-400 to-accent-emerald" />

      <div className="p-6">
        {/* Category badge + timestamp */}
        <div className="flex items-center justify-between mb-4">
          <span
            className={cn(
              "px-3 py-1 rounded-full text-xs font-semibold border",
              getCategoryColor(question_type)
            )}
          >
            {question_type.replace(/_/g, " ").toUpperCase()}
          </span>
          <span className="text-xs text-gray-500">{formatDate(decision.created_at)}</span>
        </div>

        {/* Strategy headline */}
        <div className="flex items-start gap-3 mb-4">
          <div className="p-2 rounded-lg bg-brand-500/10">
            <HiOutlineSparkles className="w-5 h-5 text-brand-400" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white leading-tight">
              {recommendation.headline}
            </h3>
            <p className="text-sm text-gray-400 mt-1">{recommendation.strategy}</p>
          </div>
        </div>

        {/* Risk gauge + confidence */}
        <div className="flex items-center gap-6 mb-5">
          <RiskGaugeInline score={risk_score.score} category={risk_score.category} />
          <div className="flex-1">
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-gray-400">Confidence</span>
              <span className="text-white font-semibold">
                {(recommendation.confidence * 100).toFixed(0)}%
              </span>
            </div>
            <div className="h-2 bg-surface-700 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${recommendation.confidence * 100}%` }}
                transition={{ duration: 0.8, delay: 0.3 }}
                className="h-full bg-gradient-to-r from-brand-500 to-brand-400 rounded-full"
              />
            </div>
          </div>
        </div>

        {/* Quant summary grid */}
        {!compact && quantitative_summary && Object.keys(quantitative_summary).length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-5">
            {Object.entries(quantitative_summary).slice(0, 6).map(([key, value]) => (
              <div
                key={key}
                className="bg-surface-800/50 rounded-xl p-3 border border-white/[0.04]"
              >
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                  {key.replace(/_/g, " ")}
                </p>
                <p className="text-sm font-bold text-white">
                  {typeof value === "number" ? formatINR(value) : String(value)}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Explanation */}
        {!compact && (
          <div className="bg-surface-800/30 rounded-xl p-4 border border-white/[0.04] mb-4">
            <p className="text-sm text-gray-300 leading-relaxed">
              {recommendation.explanation}
            </p>
          </div>
        )}

        {/* Risk factors */}
        {!compact && risk_score.top_factors && risk_score.top_factors.length > 0 && (
          <div className="mb-4">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
              Key Risk Factors
            </p>
            <div className="flex flex-wrap gap-2">
              {risk_score.top_factors.map((f, i) => (
                <span
                  key={i}
                  className={cn(
                    "px-2.5 py-1 rounded-lg text-xs font-medium border",
                    f.direction === "increases_risk"
                      ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                      : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                  )}
                >
                  {f.feature.replace(/_/g, " ")} ({f.impact.toFixed(3)})
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Disclaimer */}
        <div className="disclaimer flex items-start gap-2">
          <HiOutlineExclamationTriangle className="w-4 h-4 text-amber-500/60 flex-shrink-0 mt-0.5" />
          <span>{disclaimer || "Educational decision support only. Not financial advice."}</span>
        </div>
      </div>
    </motion.div>
  );
}

// ── Inline Risk Gauge (used inside DecisionCard) ──
function RiskGaugeInline({ score, category }: { score: number; category: string }) {
  return (
    <div className="flex items-center gap-3">
      <div className="relative w-14 h-14">
        <svg viewBox="0 0 56 56" className="w-full h-full -rotate-90">
          <circle cx="28" cy="28" r="24" fill="none" stroke="currentColor" strokeWidth="4" className="text-surface-700" />
          <motion.circle
            cx="28" cy="28" r="24"
            fill="none" strokeWidth="4" strokeLinecap="round"
            className={cn(
              score <= 30 ? "text-emerald-400" : score <= 60 ? "text-amber-400" : "text-rose-400"
            )}
            strokeDasharray={`${(score / 100) * 150.8} 150.8`}
            initial={{ strokeDasharray: "0 150.8" }}
            animate={{ strokeDasharray: `${(score / 100) * 150.8} 150.8` }}
            transition={{ duration: 1, delay: 0.2 }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={cn("text-sm font-bold", getRiskColor(score))}>{score}</span>
        </div>
      </div>
      <div>
        <p className="text-xs text-gray-500 uppercase">Risk</p>
        <p className={cn("text-sm font-semibold capitalize", getRiskColor(score))}>{category}</p>
      </div>
    </div>
  );
}
