"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { decisionApi, DecisionResponse } from "@/lib/api";
import { DecisionCard } from "@/components/decision-card";
import { motion, AnimatePresence } from "framer-motion";
import { HiOutlineSparkles, HiOutlinePaperAirplane } from "react-icons/hi2";

const SUGGESTED_QUESTIONS = [
  "Should I prepay my ₹30L home loan at 8.5% or invest the surplus in index funds?",
  "Can I afford a 6-month career break given my current savings?",
  "Am I underinsured for my 2 dependents?",
  "What happens to my portfolio if the market drops 30%?",
  "Should I increase my SIP from ₹25K to ₹40K?",
  "Is refinancing my home loan at 8.0% worth the processing fee?",
];

export default function AskPage() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<DecisionResponse | null>(null);

  const { data: history } = useQuery({
    queryKey: ["decisionHistory"],
    queryFn: async () => {
      try {
        const res = await decisionApi.getHistory();
        return res.data || [];
      } catch {
        return [];
      }
    },
  });

  const mutation = useMutation({
    mutationFn: async (q: string) => {
      const res = await decisionApi.ask({ question: q });
      return res.data;
    },
    onSuccess: (data) => {
      setResult(data);
    },
  });

  const handleAsk = (q?: string) => {
    const finalQ = q || question;
    if (!finalQ.trim()) return;
    setResult(null);
    mutation.mutate(finalQ);
    if (!q) setQuestion("");
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Ask the Engine</h1>
        <p className="text-sm text-gray-500 mt-1">
          Ask complex financial questions — get simulation-backed answers
        </p>
      </div>

      {/* Input section */}
      <div className="glass-card p-6 mb-6">
        <div className="relative">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-xl bg-brand-500/10 mt-1">
              <HiOutlineSparkles className="w-5 h-5 text-brand-400" />
            </div>
            <div className="flex-1">
              <textarea
                id="ask-input"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleAsk();
                  }
                }}
                placeholder="Ask a financial question... e.g., 'Should I prepay my home loan or invest in index funds?'"
                className="glass-input resize-none min-h-[80px]"
                rows={3}
              />
            </div>
          </div>

          <div className="flex items-center justify-between mt-4">
            <p className="text-xs text-gray-600">Press Enter to submit, Shift+Enter for new line</p>
            <button
              id="ask-submit"
              onClick={() => handleAsk()}
              disabled={!question.trim() || mutation.isPending}
              className="btn-primary"
            >
              {mutation.isPending ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <HiOutlinePaperAirplane className="w-4 h-4" />
                  Analyze
                </>
              )}
            </button>
          </div>
        </div>

        {/* Suggested chips */}
        <div className="mt-5 pt-5 border-t border-white/[0.04]">
          <p className="text-xs text-gray-500 mb-3 uppercase tracking-wider font-medium">
            Suggested Questions
          </p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_QUESTIONS.map((q, i) => (
              <button
                key={i}
                onClick={() => {
                  setQuestion(q);
                  handleAsk(q);
                }}
                className="chip text-left"
                disabled={mutation.isPending}
              >
                {q.length > 60 ? q.slice(0, 60) + "..." : q}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Loading state */}
      <AnimatePresence>
        {mutation.isPending && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="glass-card p-8 mb-6"
          >
            <div className="flex flex-col items-center gap-4">
              <div className="relative">
                <div className="w-16 h-16 border-4 border-surface-700 rounded-full" />
                <div className="absolute inset-0 w-16 h-16 border-4 border-brand-500 border-t-transparent rounded-full animate-spin" />
              </div>
              <div className="text-center">
                <p className="text-white font-semibold">Analyzing your question...</p>
                <p className="text-sm text-gray-500 mt-1">
                  Running quant models, retrieving context, scoring risk
                </p>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-600">
                <span className="w-2 h-2 rounded-full bg-brand-500 animate-pulse" />
                classify → load_profile → execute_tools → retrieve_context → score_risk → generate
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error state */}
      {mutation.isError && (
        <div className="glass-card p-6 mb-6 border-rose-500/20">
          <p className="text-rose-400 font-medium">Analysis failed</p>
          <p className="text-sm text-gray-500 mt-1">
            {(mutation.error as Error)?.message || "An unexpected error occurred. Please try again."}
          </p>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="mb-8">
          <h2 className="section-title mb-4">Analysis Result</h2>
          <DecisionCard decision={result} />
        </div>
      )}

      {/* History */}
      {history && history.length > 0 && (
        <div>
          <h2 className="section-title mb-4">Previous Decisions</h2>
          <div className="space-y-4">
            {history.map((d, i) => (
              <DecisionCard key={i} decision={d} compact />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
