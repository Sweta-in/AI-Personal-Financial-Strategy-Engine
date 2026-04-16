"use client";

import { useState, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { insuranceApi } from "@/lib/api";
import { formatINR } from "@/lib/utils";
import { RiskGauge } from "@/components/risk-gauge";
import { motion } from "framer-motion";
import {
  HiOutlineShieldCheck,
  HiOutlineShieldExclamation,
  HiOutlineDocumentArrowUp,
  HiOutlineCheckCircle,
  HiOutlineExclamationTriangle,
} from "react-icons/hi2";

export default function InsurancePage() {
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const { data: gapData } = useQuery({
    queryKey: ["insuranceGap"],
    queryFn: async () => {
      try {
        const res = await insuranceApi.getGapAnalysis();
        return res.data;
      } catch {
        return {
          required_coverage: 15000000,
          current_coverage: 7500000,
          gap: 7500000,
          adequacy_score: 50,
          annual_income: 1500000,
          age: 35,
          dependents: 2,
          outstanding_loans: 2770000,
          recommendations: [
            "Increase term life coverage by ₹75L to meet HLV requirement",
            "Consider a top-up health insurance plan of ₹10L for family",
            "Critical illness cover of ₹25L recommended given family history",
          ],
        };
      }
    },
  });

  const { data: policies } = useQuery({
    queryKey: ["policies"],
    queryFn: async () => {
      try {
        const res = await insuranceApi.getPolicies();
        return res.data;
      } catch {
        return [
          { id: "p1", type: "Term Life", provider: "LIC", coverage: 5000000, premium_annual: 12500, status: "active" },
          { id: "p2", type: "Term Life", provider: "HDFC Life", coverage: 2500000, premium_annual: 8200, status: "active" },
          { id: "p3", type: "Health", provider: "Star Health", coverage: 500000, premium_annual: 18000, status: "active" },
          { id: "p4", type: "Health", provider: "ICICI Lombard", coverage: 300000, premium_annual: 9500, status: "active" },
        ];
      }
    },
  });

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await insuranceApi.uploadPolicy(file);
      setUploadSuccess(true);
      setTimeout(() => setUploadSuccess(false), 3000);
    } catch {
      // silent
    } finally {
      setUploading(false);
    }
  };

  const adequacyScore = gapData?.adequacy_score ?? 50;
  const coverageRatio = gapData ? (gapData.current_coverage / gapData.required_coverage) * 100 : 50;

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Insurance</h1>
          <p className="text-sm text-gray-500 mt-1">Coverage analysis, gap detection, and policy management</p>
        </div>
        <div>
          <input ref={fileRef} type="file" accept=".pdf" onChange={handleUpload} className="hidden" />
          <button
            id="upload-policy-btn"
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="btn-secondary"
          >
            {uploading ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : uploadSuccess ? (
              <HiOutlineCheckCircle className="w-5 h-5 text-emerald-400" />
            ) : (
              <HiOutlineDocumentArrowUp className="w-5 h-5" />
            )}
            {uploadSuccess ? "Uploaded!" : "Upload Policy PDF"}
          </button>
        </div>
      </div>

      {/* Coverage gauge + gap summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="glass-card p-6 flex flex-col items-center justify-center">
          <h3 className="section-title mb-4">Coverage Adequacy</h3>
          <RiskGauge
            score={Math.round(100 - adequacyScore)}
            size="lg"
            label={adequacyScore >= 80 ? "Well insured" : adequacyScore >= 50 ? "Partially covered" : "Underinsured"}
          />
        </div>

        <div className="glass-card p-6 lg:col-span-2">
          <h3 className="section-title mb-4">Gap Analysis</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
            <div>
              <p className="text-xs text-gray-500 mb-1">Required (HLV)</p>
              <p className="text-lg font-bold text-white">{formatINR(gapData?.required_coverage ?? 0)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 mb-1">Current</p>
              <p className="text-lg font-bold text-emerald-400">{formatINR(gapData?.current_coverage ?? 0)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 mb-1">Gap</p>
              <p className="text-lg font-bold text-rose-400">{formatINR(gapData?.gap ?? 0)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 mb-1">Coverage Ratio</p>
              <p className="text-lg font-bold text-amber-400">{coverageRatio.toFixed(0)}%</p>
            </div>
          </div>

          {/* Coverage bar */}
          <div className="mb-6">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>Current coverage</span>
              <span>{coverageRatio.toFixed(0)}% of required</span>
            </div>
            <div className="h-3 bg-surface-700 rounded-full overflow-hidden relative">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(coverageRatio, 100)}%` }}
                transition={{ duration: 1 }}
                className={`h-full rounded-full ${
                  coverageRatio >= 80 ? "bg-emerald-500" : coverageRatio >= 50 ? "bg-amber-500" : "bg-rose-500"
                }`}
              />
              {/* Target marker */}
              <div className="absolute top-0 right-0 h-full w-0.5 bg-white/30" />
            </div>
          </div>

          {/* Recommendations */}
          {gapData?.recommendations && (
            <div className="space-y-2">
              <p className="text-xs text-gray-500 uppercase tracking-wider font-medium mb-2">Recommendations</p>
              {gapData.recommendations.map((rec: string, i: number) => (
                <div key={i} className="flex items-start gap-2 text-sm">
                  <HiOutlineExclamationTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-300">{rec}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Policies table */}
      <div className="glass-card p-6">
        <h3 className="section-title mb-4">Your Policies</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/[0.06] text-gray-500 text-xs uppercase tracking-wider">
                <th className="text-left py-3 px-2">Type</th>
                <th className="text-left py-3 px-2">Provider</th>
                <th className="text-right py-3 px-2">Coverage</th>
                <th className="text-right py-3 px-2">Annual Premium</th>
                <th className="text-center py-3 px-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {policies?.map((p: { id: string; type: string; provider: string; coverage: number; premium_annual: number; status: string }, i: number) => (
                <motion.tr
                  key={p.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors"
                >
                  <td className="py-3 px-2">
                    <div className="flex items-center gap-2">
                      {p.type === "Health" ? (
                        <HiOutlineShieldCheck className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <HiOutlineShieldExclamation className="w-4 h-4 text-brand-400" />
                      )}
                      <span className="font-medium text-white">{p.type}</span>
                    </div>
                  </td>
                  <td className="py-3 px-2 text-gray-400">{p.provider}</td>
                  <td className="py-3 px-2 text-right font-semibold text-white">{formatINR(p.coverage)}</td>
                  <td className="py-3 px-2 text-right text-gray-300">{formatINR(p.premium_annual)}/yr</td>
                  <td className="py-3 px-2 text-center">
                    <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {p.status}
                    </span>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="disclaimer">Educational decision support only. Not financial advice.</div>
    </div>
  );
}
