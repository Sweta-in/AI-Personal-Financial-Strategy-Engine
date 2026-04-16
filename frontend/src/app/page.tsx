"use client";

import { useAuthStore } from "@/lib/store";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { HiOutlineSparkles, HiOutlineChartBar, HiOutlineShieldCheck, HiOutlineBolt } from "react-icons/hi2";

export default function HomePage() {
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated) router.replace("/dashboard");
  }, [isAuthenticated, router]);

  return (
    <div className="min-h-screen bg-surface-950 flex flex-col">
      {/* Hero */}
      <main className="flex-1 flex items-center justify-center relative overflow-hidden">
        {/* Background effects */}
        <div className="absolute inset-0 bg-gradient-mesh" />
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-500/10 rounded-full blur-[100px]" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-accent-emerald/10 rounded-full blur-[100px]" />

        <div className="relative z-10 max-w-4xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
          >
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-500/10
              border border-brand-500/20 mb-8">
              <HiOutlineBolt className="w-4 h-4 text-brand-400" />
              <span className="text-sm font-medium text-brand-300">
                AI-Powered Financial Intelligence
              </span>
            </div>

            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white mb-6 leading-[1.1]">
              Your Money.{" "}
              <span className="text-gradient">Quantified.</span>
              <br />
              <span className="text-gray-400">Simulated. Decided.</span>
            </h1>

            <p className="text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
              Stop guessing. Ask complex financial questions and get simulation-backed,
              explainable recommendations grounded in your actual numbers.
            </p>

            <div className="flex items-center justify-center gap-4">
              <Link href="/register" className="btn-primary text-lg px-8 py-4">
                Get Started Free
              </Link>
              <Link href="/login" className="btn-secondary text-lg px-8 py-4">
                Sign In
              </Link>
            </div>
          </motion.div>

          {/* Feature cards */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.3 }}
            className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-20"
          >
            <FeatureCard
              icon={<HiOutlineChartBar className="w-6 h-6 text-brand-400" />}
              title="Monte Carlo Simulations"
              desc="10,000-path portfolio projections with P10/P50/P90 confidence bands"
            />
            <FeatureCard
              icon={<HiOutlineSparkles className="w-6 h-6 text-emerald-400" />}
              title="Multi-Agent Reasoning"
              desc="LangGraph orchestrator with quant tools, RAG, and ML risk scoring"
            />
            <FeatureCard
              icon={<HiOutlineShieldCheck className="w-6 h-6 text-amber-400" />}
              title="Insurance Gap Analysis"
              desc="HLV-based coverage detection with policy-level RAG retrieval"
            />
          </motion.div>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-6 border-t border-white/[0.04]">
        <p className="text-center text-xs text-gray-600">
          Educational decision support only. Not financial advice.
        </p>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, desc }: { icon: React.ReactNode; title: string; desc: string }) {
  return (
    <div className="glass-card p-5 text-left group">
      <div className="p-2.5 rounded-xl bg-surface-800/60 w-fit mb-3 group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <h3 className="text-sm font-bold text-white mb-1.5">{title}</h3>
      <p className="text-xs text-gray-500 leading-relaxed">{desc}</p>
    </div>
  );
}
