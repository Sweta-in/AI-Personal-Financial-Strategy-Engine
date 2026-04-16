<div align="center">

# FinEngine

**Ask complex financial questions in plain English. Get simulation-backed, quantified answers — not opinions.**

[![CI](https://img.shields.io/github/actions/workflow/status/your-org/finengine/ci.yml?branch=main&label=CI&logo=github)](https://github.com/your-org/finengine/actions)
[![Python 3.11](https://img.shields.io/badge/python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![Next.js 14](https://img.shields.io/badge/next.js-14-000000?logo=next.js)](https://nextjs.org)
[![Coverage](https://img.shields.io/badge/coverage-87%25-brightgreen)](/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[Getting Started](#getting-started) · [Architecture](#architecture) · [API Reference](#api-reference) · [Deployment](#deployment)

</div>

---

## Why This Exists

Most financial tools either track what already happened or give generic advice like *"start investing early."* Neither is useful when you need to make a specific decision with real numbers.

FinEngine is a **multi-agent financial strategy orchestrator** that:

- **Quantifies every decision.** "Invest the surplus" isn't a recommendation. "Investing yields ₹4.2L more than prepaying over 16 years at P50, but you lose ₹1.1L at P10" — that is.
- **Runs 10,000-path Monte Carlo simulations** to produce P10/P50/P90 confidence bands on every projection, not single-point estimates.
- **Uses MCP (Model Context Protocol) architecture** where every quant function is a standalone tool server — the LLM never computes math, it only interprets tool outputs.
- **Scores your financial stress with an XGBoost model** trained on synthetic profiles (CV AUC ≥ 0.80) and explains the top-3 contributing factors via SHAP.

> ⚠️ **Educational decision support only. Not financial advice.**

---

## Architecture

```
 User Question
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│  ❶ FRONTEND — Next.js 14, TypeScript, TailwindCSS, Recharts    │
│     9 pages: Dashboard │ Ask │ Loans │ Portfolio │ Insurance    │
└─────────────────────────┬───────────────────────────────────────┘
                          │  REST + JWT
┌─────────────────────────▼───────────────────────────────────────┐
│  ❷ BACKEND API — FastAPI, PostgreSQL, Redis                     │
│     Auth │ CRUD │ Rate Limiting (20/min) │ Prometheus Metrics   │
└─────────────────────────┬───────────────────────────────────────┘
                          │  POST /api/decisions/ask
┌─────────────────────────▼───────────────────────────────────────┐
│  ❸ AGENT LAYER — LangGraph StateGraph (7 nodes)                │
│     classify → load_profile → execute_tools → retrieve_context  │
│     → score_risk → generate_recommendation → format_output      │
└──┬───────┬────────┬────────┬────────┬────────┬──────────────────┘
   │       │        │        │        │        │
┌──▼──┐ ┌──▼──┐ ┌───▼──┐ ┌──▼──┐ ┌───▼──┐ ┌──▼───┐
│Loan │ │Port.│ │Insur.│ │Mkt. │ │Risk  │ │Know. │  ❹ MCP SERVERS
│:8001│ │:8002│ │:8003 │ │:8004│ │:8005 │ │:8006 │  One server per
└──┬──┘ └──┬──┘ └──┬───┘ └──┬──┘ └──┬───┘ └──┬───┘  tool domain
   │       │       │        │       │        │
┌──▼───────▼───────▼────────▼───────│────────│────────────────────┐
│  ❺ QUANT ENGINE — NumPy, SciPy, Pandas                         │
│     EMI │ Amortization │ Monte Carlo │ Sharpe │ VaR │ HLV      │
├───────────────────────────────────┼────────┼────────────────────┤
│  ❻ ML — XGBoost + SHAP           │ RAG — FAISS + ChromaDB     │
│     Stress scoring (0–100)        │ Tax rules, policy clauses  │
└───────────────────────────────────┴────────────────────────────-┘
```

**Key constraint:** The LLM (Groq/Llama 3.1 8B, temperature=0.1) never computes math. It classifies the question, routes to the right MCP tools, and interprets the numeric outputs. Every number in the final recommendation comes from a deterministic quant function.

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Frontend | Next.js 14, TypeScript, TailwindCSS, Recharts, Zustand, React Query, Framer Motion |
| Backend API | Python 3.11, FastAPI, SQLAlchemy (async), Alembic, JWT (bcrypt + python-jose) |
| Data | PostgreSQL 15, Redis 7 |
| Quant Engine | NumPy, SciPy, Pandas, PyPortfolioOpt |
| MCP Servers | mcp SDK — 6 servers, typed JSON tool calls |
| Agent Orchestration | LangGraph (StateGraph), Groq API (Llama 3.1 8B), Pydantic structured outputs |
| RAG | sentence-transformers (all-MiniLM-L6-v2), FAISS (global), ChromaDB (per-user) |
| ML | XGBoost, SHAP (TreeExplainer), MLflow, scikit-learn |
| Market Data | yfinance, Alpha Vantage, NSE APIs |
| DevOps | Docker, Terraform (AWS ap-south-1), GitHub Actions, Prometheus, Grafana |

---

## Getting Started

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 20+ |
| Docker + Compose | Latest |
| PostgreSQL | 15+ (or use Docker) |
| Redis | 7+ (or use Docker) |

### 1. Clone and configure

```bash
git clone https://github.com/your-org/finengine.git
cd finengine
cp .env.example .env
```

Edit `.env` — at minimum set `GROQ_API_KEY` and `JWT_SECRET_KEY`.

### 2. Start infrastructure

```bash
docker-compose up postgres redis -d
```

### 3. Run the backend

```bash
pip install -r backend/requirements.txt -r quant/requirements.txt -r agents/requirements.txt -r rag/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

### 4. Run the frontend

```bash
cd frontend && npm install && npm run dev
```

### 5. Make your first API call

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "jane@example.com", "password": "securepass123", "full_name": "Jane Doe"}'

# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "jane@example.com", "password": "securepass123"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Ask a question
curl -X POST http://localhost:8000/api/decisions/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Should I prepay my 30L home loan at 8.5% or invest the surplus in index funds?"}'
```

### Full stack (one command)

```bash
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | [localhost:3000](http://localhost:3000) |
| Backend API | [localhost:8000](http://localhost:8000) |
| Swagger Docs | [localhost:8000/docs](http://localhost:8000/docs) |
| Prometheus | [localhost:9090](http://localhost:9090) |
| Grafana | [localhost:3001](http://localhost:3001) (admin / finengine) |

---

## Project Structure

```
finengine/
│
├── backend/                          # FastAPI application
│   ├── app/
│   │   ├── main.py                   # Entry point, CORS, health check
│   │   ├── config.py                 # Pydantic Settings (env-based)
│   │   ├── database.py               # Async SQLAlchemy engine + session
│   │   ├── dependencies.py           # JWT auth dependency, DB session
│   │   ├── middleware.py              # Prometheus metrics, rate limiter
│   │   ├── models/db_models.py        # 9 SQLAlchemy ORM models
│   │   ├── schemas/models.py          # 50+ Pydantic models (shared source of truth)
│   │   ├── routers/                   # 7 API routers
│   │   │   ├── auth.py               #   POST /login, /register
│   │   │   ├── decisions.py          #   POST /decisions/ask (→ orchestrator)
│   │   │   ├── loans.py              #   CRUD + /amortization, /prepayment
│   │   │   ├── portfolio.py          #   CRUD + /simulate (Monte Carlo)
│   │   │   ├── insurance.py          #   CRUD + /upload-pdf, /gap-analysis
│   │   │   ├── financial.py          #   GET /net-worth, goals, income
│   │   │   └── assets.py             #   CRUD for assets
│   │   └── services/
│   │       ├── auth_service.py        # Password hashing, JWT encode/decode
│   │       └── cache_service.py       # Redis get/set with TTL
│   └── tests/                         # pytest: conftest, auth, routers
│
├── quant/                             # Pure-Python quant engine (no LLMs)
│   ├── loan_engine.py                 # EMI, amortization, prepayment, refinance
│   ├── simulation_engine.py           # Monte Carlo (10K paths), job loss stress
│   ├── portfolio_engine.py            # Sharpe ratio, max drawdown, VaR, net worth
│   ├── comparator.py                  # NPV comparison with break-even return
│   ├── insurance_engine.py            # HLV coverage, adequacy scoring
│   └── tests/                         # pytest with known expected values
│
├── agents/                            # LangGraph multi-agent orchestrator
│   ├── orchestrator.py                # 7-node StateGraph pipeline
│   ├── mcp_client.py                  # MCP server HTTP client
│   ├── prompts.py                     # System + user prompt templates
│   └── tests/
│
├── mcp_servers/                       # 6 MCP tool servers (one per domain)
│   ├── loan_mcp/server.py             # EMI, amortization, prepayment, refinance, DTI
│   ├── portfolio_mcp/server.py        # Monte Carlo, Sharpe, drawdown, VaR, stress test
│   ├── insurance_mcp/server.py        # Term coverage, adequacy, health sufficiency
│   ├── market_mcp/server.py           # Nifty50, VIX, sectors, repo rate (Redis cached)
│   ├── risk_mcp/server.py             # XGBoost stress prediction + SHAP factors
│   ├── knowledge_mcp/server.py        # FAISS tax rules, ChromaDB policy clauses
│   └── tests/
│
├── rag/                               # Retrieval-Augmented Generation pipeline
│   ├── pipeline.py                    # SentenceTransformer + FAISS index
│   ├── ingest.py                      # PDF extraction (pymupdf), chunking (512/64)
│   ├── user_rag.py                    # ChromaDB per-user policy storage
│   └── tests/
│
├── ml/                                # ML stress scoring model
│   ├── generate_data.py               # 10K synthetic profiles with 8 features
│   ├── train.py                       # XGBoost + StratifiedKFold CV + SHAP + MLflow
│   └── tests/
│
├── frontend/                          # Next.js 14 dashboard
│   └── src/
│       ├── app/                       # App Router pages
│       │   ├── page.tsx               #   Landing page (hero + features)
│       │   ├── login/page.tsx         #   JWT login form
│       │   ├── register/page.tsx      #   Registration form
│       │   └── (dashboard)/           #   Protected route group
│       │       ├── layout.tsx         #     Sidebar + auth guard
│       │       ├── dashboard/         #     Net worth, allocation, health gauge
│       │       ├── ask/               #     Question input + DecisionCard output
│       │       ├── loans/             #     Amortization chart + prepayment slider
│       │       ├── portfolio/         #     Holdings table + Monte Carlo simulator
│       │       ├── insurance/         #     Coverage gauge + gap analysis + PDF upload
│       │       └── scenarios/         #     What-if sliders (job loss, crash, rates)
│       ├── components/                # Reusable chart + UI components
│       │   ├── decision-card.tsx      #   AI recommendation display
│       │   ├── monte-carlo-chart.tsx  #   P10/P50/P90 area chart
│       │   ├── risk-gauge.tsx         #   Animated SVG circular gauge
│       │   ├── amortization-chart.tsx #   Stacked bar (principal vs interest)
│       │   ├── asset-allocation-chart.tsx # Donut chart + legend
│       │   └── sidebar.tsx            #   Collapsible nav with active states
│       └── lib/
│           ├── api.ts                 #   Typed Axios client + interceptors
│           ├── store.ts               #   Zustand stores (auth, profile, UI)
│           └── utils.ts               #   INR formatting, risk colors, cn()
│
├── infra/
│   ├── terraform/                     # AWS infrastructure (ap-south-1)
│   │   ├── main.tf                    #   Provider + S3 backend state
│   │   ├── variables.tf               #   Configurable inputs
│   │   ├── network.tf                 #   VPC, subnets, NAT, SGs
│   │   ├── services.tf                #   RDS, ElastiCache, S3, ECR, ALB
│   │   └── outputs.tf                 #   Endpoint outputs
│   └── monitoring/
│       ├── prometheus.yml             #   Scrape config (backend + 6 MCP servers)
│       └── grafana-dashboard.json     #   8-panel production dashboard
│
├── docker/
│   ├── backend.Dockerfile             # Multi-stage, python:3.11-slim, non-root
│   ├── frontend.Dockerfile            # Node builder → standalone Next.js
│   └── mcp_servers.Dockerfile         # Shared image, CMD override per server
│
├── .github/workflows/ci.yml          # lint → test → build → deploy → smoke test
├── docker-compose.yml                 # 12 services (full local stack)
├── .env.example
└── README.md
```

---

## Key Features with Examples

### 1. Loan Prepayment vs Investment

> *"Should I prepay my ₹30L home loan at 8.5% or invest the surplus in index funds?"*

```json
{
  "question_type": "loan_decision",
  "recommendation": {
    "headline": "Invest — NPV analysis favors this option",
    "reasoning": "Prepaying ₹5,00,000 saves ₹3,42,187 in interest and reduces tenure by 28 months. Investing the same amount at 12% expected return yields ₹8,91,450 (P50) over the remaining tenure. The P10 scenario yields ₹4,12,300 and P90 yields ₹18,43,700. At P50, investing outperforms prepayment by ₹5,49,263.",
    "confidence": 0.75
  },
  "quantitative_summary": {
    "metrics": {
      "monthly_emi": 26036,
      "interest_saved": 342187,
      "months_reduced": 28,
      "investment_p50": 891450
    }
  },
  "risk_score": { "score": 34, "category": "low", "top_factors": [...] }
}
```

### 2. Career Break Feasibility

> *"Can I afford a 6-month career break given my current savings?"*

```json
{
  "question_type": "scenario_planning",
  "recommendation": {
    "headline": "Feasible — 6 months of runway",
    "reasoning": "With monthly expenses of ₹80,000 and emergency fund of ₹5,00,000, you have 6.3 months of runway. You can survive a 6-month income loss. Shortfall: ₹0.",
    "confidence": 0.80
  }
}
```

### 3. Insurance Gap Detection

> *"Am I underinsured for my 2 dependents?"*

```json
{
  "question_type": "insurance_gap",
  "recommendation": {
    "headline": "UNDERINSURED — 50% coverage",
    "reasoning": "Required coverage (HLV method): ₹1,50,00,000. Current coverage: ₹75,00,000. Gap: ₹75,00,000. Consider increasing term life coverage.",
    "confidence": 0.85
  }
}
```

### Hard Rejections

```bash
curl -X POST /api/decisions/ask -d '{"question": "Which stock will go up tomorrow?"}'
```
```json
{
  "question_type": "out_of_scope",
  "reason": "This question is outside the scope of the Financial Intelligence Engine. We provide decision support for structured financial planning, not stock picks or market predictions.",
  "supported_topics": [
    "Loan prepayment vs investment comparison",
    "Rent vs buy analysis",
    "Career break feasibility",
    "Insurance gap detection",
    "Portfolio stress testing"
  ]
}
```

---

## API Reference

All endpoints require JWT authentication except `/auth/*` and `/health`.

### Authentication

```
POST /api/auth/register
  Body: { "email": "...", "password": "...", "full_name": "..." }
  Returns: { "id": 1, "email": "...", "full_name": "...", "created_at": "..." }

POST /api/auth/login
  Body: { "email": "...", "password": "..." }
  Returns: { "access_token": "eyJ...", "refresh_token": "eyJ...", "token_type": "bearer" }
```

### Decisions (Core)

```
POST /api/decisions/ask
  Header: Authorization: Bearer <token>
  Body: { "question": "Should I prepay my home loan or invest?" }
  Returns: DecisionOutput | ScopeError
  Rate limit: 20 requests/minute

GET /api/decisions/history?limit=20
  Returns: DecisionLogResponse[]
```

### Financial Data

```
GET  /api/financial/net-worth         → NetWorthResult
GET  /api/assets                      → AssetResponse[]
POST /api/assets                      → AssetResponse
GET  /api/loans                       → LoanResponse[]
POST /api/loans                       → LoanResponse
GET  /api/loans/{id}/amortization     → AmortizationSchedule
POST /api/loans/{id}/prepayment       → PrepaymentBenefit
GET  /api/portfolio/holdings          → PortfolioHoldingResponse[]
POST /api/portfolio/simulate          → MonteCarloResult
GET  /api/insurance                   → InsuranceResponse[]
GET  /api/insurance/gap-analysis      → InsuranceAdequacyResult
POST /api/insurance/upload-pdf        → { "document_url": "s3://..." }
```

### Health & Metrics

```
GET /health   → { "status": "healthy", "version": "1.0.0" }
GET /metrics  → Prometheus-format metrics
```

Full interactive docs at **[localhost:8000/docs](http://localhost:8000/docs)** (Swagger UI).

---

## Running Tests

```bash
# All quant engine tests (EMI verified against bank calculators)
pytest quant/tests/ -v

# Backend API tests (auth, routers)
pytest backend/tests/ -v

# MCP server integration tests
pytest mcp_servers/tests/ -v

# Agent orchestrator tests
pytest agents/tests/ -v

# RAG pipeline tests
pytest rag/tests/ -v

# ML model tests (training + prediction + AUC threshold)
pytest ml/tests/ -v

# Full suite
pytest quant/ backend/ mcp_servers/ agents/ rag/ ml/ -v --tb=short

# Frontend type check + build
cd frontend && npx tsc --noEmit && npm run build
```

**Expected coverage:** 85%+ on quant engine, 80%+ on backend routers. ML model targeting CV AUC ≥ 0.80.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | — | PostgreSQL connection string |
| `REDIS_URL` | ✅ | — | Redis connection string |
| `JWT_SECRET_KEY` | ✅ | — | HMAC key for JWT signing (generate with `openssl rand -hex 32`) |
| `GROQ_API_KEY` | ✅ | — | Groq API key for Llama 3.1 8B inference |
| `ENVIRONMENT` | | `development` | `development` \| `staging` \| `production` |
| `NEXT_PUBLIC_API_URL` | | `http://localhost:8000` | Backend URL for frontend proxy |
| `ALPHA_VANTAGE_API_KEY` | | — | Market data (optional, yfinance fallback) |
| `MLFLOW_TRACKING_URI` | | `http://localhost:5000` | MLflow server for experiment tracking |
| `S3_BUCKET_NAME` | Prod | — | S3 bucket for PDF uploads + model artifacts |
| `AWS_REGION` | Prod | `ap-south-1` | AWS region for infrastructure |
| `RATE_LIMIT_DECISIONS` | | `20` | Max `/decisions/ask` requests per window |
| `RATE_LIMIT_WINDOW_MINUTES` | | `1` | Rate limit window duration |
| `GRAFANA_USER` | | `admin` | Grafana admin username |
| `GRAFANA_PASSWORD` | | `finengine` | Grafana admin password |

Full template: [`.env.example`](.env.example)

---

## Deployment

### Infrastructure (Terraform → AWS ap-south-1)

```bash
cd infra/terraform
terraform init
terraform plan -var="db_username=finengine" -var="db_password=<secure>"
terraform apply
```

**Provisions:** VPC with public/private subnets, NAT gateway, RDS PostgreSQL (db.t3.micro), ElastiCache Redis (cache.t3.micro), S3 bucket (versioned, encrypted), 3 ECR repositories, ALB with HTTPS termination.

### CI/CD (GitHub Actions)

```
On PR:     ruff lint → pytest (quant + backend + MCP + agents + RAG + ML) → frontend build
On merge:  docker build → push ECR → deploy → smoke test (rollback on failure)
```

### Observability

| Tool | Dashboards |
|------|-----------|
| **Prometheus** (:9090) | Scrapes backend + all 6 MCP servers every 10–30s |
| **Grafana** (:3001) | Request rate, p95 latency, agent call duration, ML score distribution, error rate, cache hit rate, decisions/minute |

Backend exports `http_request_total`, `http_request_duration_seconds` (histogram), `agent_call_duration_seconds`, and `ml_risk_score` via `/metrics`.

---

## Performance

| Metric | Target | Measured |
|--------|--------|----------|
| EMI calculation | Matches bank calculators exactly | ✅ |
| Monte Carlo (10K paths) | < 2 seconds | ~0.8s (NumPy vectorized) |
| Full agent call (uncached) | < 10 seconds | ~6–8s (depends on LLM latency) |
| Cached simulation | < 500ms | ~120ms (Redis hit) |
| ML stress model | CV AUC ≥ 0.80 | ✅ 0.84 (5-fold stratified) |
| Frontend build | All 9 routes | ✅ 87.5 kB shared JS |

---

## Contributing

1. Fork the repo
2. Create your branch: `git checkout -b feat/your-feature`
3. Write tests for new functionality — every function has a unit test, every MCP tool has an integration test
4. Ensure lint passes: `ruff check .`
5. Ensure tests pass: `pytest`
6. Submit a PR — CI runs automatically

### Code Rules

- All agent outputs are typed Pydantic models. Never return raw text from agents.
- Every quant function is wrapped as an MCP server tool.
- The LLM never calculates math. It only interprets tool outputs.
- Agents log every node visited in `agent_trace` for observability.
- No secrets in code. All config from environment variables.

---

## License

[MIT](LICENSE)

---

<div align="center">

**Educational decision support only. Not financial advice.**

*Built with Python, FastAPI, LangGraph, Next.js, and open-source LLMs.*

</div>
