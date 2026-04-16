/**
 * API client — Axios wrapper for backend communication.
 * All endpoints typed. Token injected from Zustand auth store.
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// Inject JWT from localStorage
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle 401 → redirect to login
api.interceptors.response.use(
  (res) => res,
  (err: AxiosError) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// ── Auth ──
export const authApi = {
  login: (email: string, password: string) =>
    api.post<{ access_token: string; token_type: string }>("/api/auth/login", {
      email,
      password,
    }),
  register: (email: string, password: string, full_name: string) =>
    api.post<{ id: string; email: string }>("/api/auth/register", {
      email,
      password,
      full_name,
    }),
};

// ── Financial ──
export const financialApi = {
  getNetWorth: () => api.get("/api/financial/net-worth"),
  getAssets: () => api.get("/api/assets"),
  createAsset: (data: Record<string, unknown>) => api.post("/api/assets", data),
  getLoans: () => api.get("/api/loans"),
  createLoan: (data: Record<string, unknown>) => api.post("/api/loans", data),
  getLoanAmortization: (loanId: string) =>
    api.get(`/api/loans/${loanId}/amortization`),
  simulatePrepayment: (loanId: string, amount: number) =>
    api.post(`/api/loans/${loanId}/prepayment`, { prepayment_amount: amount }),
};

// ── Portfolio ──
export const portfolioApi = {
  getHoldings: () => api.get("/api/portfolio/holdings"),
  getMetrics: () => api.get("/api/portfolio/metrics"),
  monteCarloSimulation: (params: {
    initial_value: number;
    monthly_sip: number;
    annual_return_mean: number;
    annual_return_std: number;
    time_horizon_months: number;
  }) => api.post("/api/portfolio/simulate", params),
};

// ── Insurance ──
export const insuranceApi = {
  getPolicies: () => api.get("/api/insurance"),
  uploadPolicy: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/api/insurance/upload-pdf", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  getGapAnalysis: () => api.get("/api/insurance/gap-analysis"),
};

// ── Decisions — the core ──
export interface DecisionRequest {
  question: string;
}

export interface DecisionResponse {
  decision_id: string;
  question: string;
  question_type: string;
  recommendation: {
    headline: string;
    strategy: string;
    explanation: string;
    confidence: number;
  };
  quantitative_summary: Record<string, unknown>;
  risk_score: {
    score: number;
    category: string;
    top_factors: Array<{ feature: string; impact: number; direction: string }>;
  };
  agent_trace: string[];
  disclaimer: string;
  created_at: string;
}

export const decisionApi = {
  ask: (data: DecisionRequest) =>
    api.post<DecisionResponse>("/api/decisions/ask", data),
  getHistory: () => api.get<DecisionResponse[]>("/api/decisions/history"),
  getById: (id: string) =>
    api.get<DecisionResponse>(`/api/decisions/${id}`),
};

// ── Scenarios ──
export const scenarioApi = {
  jobLossStressTest: (params: {
    monthly_expenses: number;
    emergency_fund: number;
    income_loss_months: number;
  }) => api.post("/api/scenarios/job-loss", params),
  marketCrashTest: (params: {
    portfolio_value: number;
    drop_percent: number;
  }) => api.post("/api/scenarios/market-crash", params),
  rateChangeTest: (params: {
    loan_outstanding: number;
    current_rate: number;
    new_rate: number;
    remaining_months: number;
  }) => api.post("/api/scenarios/rate-change", params),
};
