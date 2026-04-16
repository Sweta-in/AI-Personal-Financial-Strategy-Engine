"use client";

import { getRiskColor, getRiskBgColor, cn } from "@/lib/utils";
import { motion } from "framer-motion";

interface RiskGaugeProps {
  score: number;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  label?: string;
}

export function RiskGauge({ score, size = "md", showLabel = true, label }: RiskGaugeProps) {
  const sizes = {
    sm: { svg: 80, radius: 32, stroke: 5, text: "text-lg" },
    md: { svg: 120, radius: 48, stroke: 6, text: "text-2xl" },
    lg: { svg: 160, radius: 64, stroke: 8, text: "text-3xl" },
  };

  const s = sizes[size];
  const circumference = 2 * Math.PI * s.radius;
  const dashArray = (score / 100) * circumference;

  const category = score <= 30 ? "Low Risk" : score <= 60 ? "Medium Risk" : "High Risk";

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: s.svg, height: s.svg }}>
        <svg
          viewBox={`0 0 ${s.svg} ${s.svg}`}
          className="w-full h-full"
          style={{ transform: "rotate(-90deg)" }}
        >
          {/* Background circle */}
          <circle
            cx={s.svg / 2}
            cy={s.svg / 2}
            r={s.radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={s.stroke}
            className="text-surface-700"
          />
          {/* Progress arc */}
          <motion.circle
            cx={s.svg / 2}
            cy={s.svg / 2}
            r={s.radius}
            fill="none"
            strokeWidth={s.stroke}
            strokeLinecap="round"
            className={cn(
              score <= 30
                ? "text-emerald-400"
                : score <= 60
                ? "text-amber-400"
                : "text-rose-400"
            )}
            initial={{ strokeDasharray: `0 ${circumference}` }}
            animate={{ strokeDasharray: `${dashArray} ${circumference}` }}
            transition={{ duration: 1.2, ease: "easeOut" }}
          />
        </svg>
        {/* Center score */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            className={cn(s.text, "font-bold", getRiskColor(score))}
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            {score}
          </motion.span>
          {size !== "sm" && (
            <span className="text-[10px] text-gray-500 uppercase tracking-widest">
              / 100
            </span>
          )}
        </div>
      </div>

      {showLabel && (
        <div className="text-center">
          <p className={cn("text-sm font-semibold", getRiskColor(score))}>{category}</p>
          {label && <p className="text-xs text-gray-500 mt-0.5">{label}</p>}
        </div>
      )}
    </div>
  );
}
