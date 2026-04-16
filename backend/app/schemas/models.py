"""
Personal Financial Intelligence Engine — Shared Pydantic Schemas

ALL modules import from this single source of truth.
Every agent output, quant result, and API response is a typed Pydantic model.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# ENUMS
# ============================================================

class QuestionType(str, Enum):
    LOAN_DECISION = "loan_decision"
    PORTFOLIO_RISK = "portfolio_risk"
    INSURANCE_GAP = "insurance_gap"
    SCENARIO_PLANNING = "scenario_planning"
    MARKET_CONTEXT = "market_context"
    OUT_OF_SCOPE = "out_of_scope"


class RiskCategory(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LoanType(str, Enum):
    HOME = "home"
    PERSONAL = "personal"
    CAR = "car"
    EDUCATION = "education"
    OTHER = "other"


class AssetType(str, Enum):
    EQUITY = "equity"
    DEBT = "debt"
    REAL_ESTATE = "real_estate"
    GOLD = "gold"
    CASH = "cash"
    FIXED_DEPOSIT = "fixed_deposit"
    PPF = "ppf"
    NPS = "nps"
    OTHER = "other"


class InsuranceType(str, Enum):
    TERM_LIFE = "term_life"
    HEALTH = "health"
    ENDOWMENT = "endowment"
    ULIP = "ulip"
    OTHER = "other"


class GoalStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class IncomeFrequency(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


# ============================================================
# AUTH SCHEMAS
# ============================================================

class UserCreate(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    full_name: str = Field(..., min_length=1, description="Full name")


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: int
    exp: datetime


# ============================================================
# FINANCIAL ENTITY SCHEMAS — Request/Response
# ============================================================

# --- Loan ---

class LoanCreate(BaseModel):
    name: str = Field(..., description="Loan identifier, e.g. 'SBI Home Loan'")
    loan_type: LoanType
    principal: float = Field(..., gt=0)
    annual_rate: float = Field(..., gt=0, le=50, description="Annual interest rate in %")
    tenure_months: int = Field(..., gt=0, le=600)
    outstanding_balance: float = Field(..., ge=0)
    emi: Optional[float] = None
    start_date: Optional[datetime] = None


class LoanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    loan_type: LoanType
    principal: float
    annual_rate: float
    tenure_months: int
    outstanding_balance: float
    emi: Optional[float]
    start_date: Optional[datetime]
    created_at: datetime


class LoanUpdate(BaseModel):
    name: Optional[str] = None
    outstanding_balance: Optional[float] = None
    annual_rate: Optional[float] = None
    emi: Optional[float] = None


# --- Insurance ---

class InsuranceCreate(BaseModel):
    name: str
    insurance_type: InsuranceType
    provider: str
    sum_assured: float = Field(..., gt=0)
    annual_premium: float = Field(..., gt=0)
    policy_start: Optional[datetime] = None
    policy_end: Optional[datetime] = None
    document_url: Optional[str] = None


class InsuranceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    insurance_type: InsuranceType
    provider: str
    sum_assured: float
    annual_premium: float
    policy_start: Optional[datetime]
    policy_end: Optional[datetime]
    document_url: Optional[str]
    created_at: datetime


class InsuranceUpdate(BaseModel):
    name: Optional[str] = None
    sum_assured: Optional[float] = None
    annual_premium: Optional[float] = None
    document_url: Optional[str] = None


# --- Asset ---

class AssetCreate(BaseModel):
    name: str
    asset_type: AssetType
    current_value: float = Field(..., ge=0)
    invested_value: Optional[float] = Field(None, ge=0)
    annual_return_pct: Optional[float] = None


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    asset_type: AssetType
    current_value: float
    invested_value: Optional[float]
    annual_return_pct: Optional[float]
    created_at: datetime


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    current_value: Optional[float] = None
    annual_return_pct: Optional[float] = None


# --- Income Source ---

class IncomeSourceCreate(BaseModel):
    name: str = Field(..., description="e.g. 'Salary - TCS', 'Freelance'")
    amount: float = Field(..., gt=0)
    frequency: IncomeFrequency
    is_active: bool = True


class IncomeSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    amount: float
    frequency: IncomeFrequency
    is_active: bool
    created_at: datetime


# --- Portfolio Holding ---

class PortfolioHoldingCreate(BaseModel):
    symbol: str = Field(..., description="Ticker symbol, e.g. 'NIFTYBEES.NS'")
    name: str
    asset_type: AssetType
    quantity: float = Field(..., gt=0)
    avg_buy_price: float = Field(..., gt=0)
    current_price: Optional[float] = None


class PortfolioHoldingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    symbol: str
    name: str
    asset_type: AssetType
    quantity: float
    avg_buy_price: float
    current_price: Optional[float]
    created_at: datetime


# --- Financial Goal ---

class FinancialGoalCreate(BaseModel):
    name: str = Field(..., description="e.g. 'Retirement Fund', 'Child Education'")
    target_amount: float = Field(..., gt=0)
    current_amount: float = Field(0, ge=0)
    target_date: Optional[datetime] = None
    monthly_contribution: Optional[float] = Field(None, ge=0)
    status: GoalStatus = GoalStatus.ACTIVE


class FinancialGoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    target_amount: float
    current_amount: float
    target_date: Optional[datetime]
    monthly_contribution: Optional[float]
    status: GoalStatus
    created_at: datetime


class FinancialGoalUpdate(BaseModel):
    current_amount: Optional[float] = None
    monthly_contribution: Optional[float] = None
    status: Optional[GoalStatus] = None


# ============================================================
# QUANT ENGINE OUTPUT SCHEMAS
# ============================================================

class EMIResult(BaseModel):
    """Output of calculate_emi()"""
    principal: float
    annual_rate: float
    tenure_months: int
    monthly_emi: float
    total_payment: float
    total_interest: float


class AmortizationRow(BaseModel):
    """Single row in an amortization schedule"""
    month: int
    opening_balance: float
    emi: float
    principal_component: float
    interest_component: float
    closing_balance: float


class AmortizationSchedule(BaseModel):
    """Full amortization schedule output"""
    principal: float
    annual_rate: float
    tenure_months: int
    monthly_emi: float
    schedule: list[AmortizationRow]
    total_interest: float
    total_payment: float


class PrepaymentBenefit(BaseModel):
    """Output of calculate_prepayment_benefit()"""
    prepayment_amount: float
    interest_saved: float
    months_reduced: int
    new_tenure_months: int
    original_total_interest: float
    new_total_interest: float


class RefinanceResult(BaseModel):
    """Output of refinance_break_even()"""
    old_rate: float
    new_rate: float
    processing_fee: float
    monthly_savings: float
    break_even_months: int
    total_savings_over_tenure: float
    recommendation: str


class SimulationPercentiles(BaseModel):
    """Percentile values from Monte Carlo simulation"""
    p10: float
    p50: float
    p90: float


class MonteCarloResult(BaseModel):
    """Output of monte_carlo_portfolio_growth()"""
    initial_value: float
    monthly_sip: float
    time_horizon_months: int
    n_simulations: int
    annual_return_mean: float
    annual_return_std: float
    final_value: SimulationPercentiles
    monthly_values_p10: list[float]
    monthly_values_p50: list[float]
    monthly_values_p90: list[float]


class JobLossStressResult(BaseModel):
    """Output of job_loss_stress_test()"""
    monthly_expenses: float
    emergency_fund: float
    income_loss_months: int
    months_of_runway: float
    survives: bool
    shortfall: float
    depletion_schedule: list[float]


class SharpeRatioResult(BaseModel):
    """Output of calculate_sharpe_ratio()"""
    sharpe_ratio: float
    annualized_return: float
    annualized_volatility: float
    risk_free_rate: float


class MaxDrawdownResult(BaseModel):
    """Output of calculate_max_drawdown()"""
    max_drawdown: float
    peak_value: float
    trough_value: float
    peak_index: int
    trough_index: int


class VaRResult(BaseModel):
    """Output of calculate_var()"""
    var_value: float
    confidence: float
    interpretation: str


class NetWorthResult(BaseModel):
    """Output of net_worth()"""
    total_assets: float
    total_liabilities: float
    net_worth: float
    asset_breakdown: dict[str, float]
    liability_breakdown: dict[str, float]


class NPVComparisonResult(BaseModel):
    """Output of npv_comparison()"""
    npv_a: float
    npv_b: float
    label_a: str
    label_b: str
    winner: str
    difference: float
    break_even_return: Optional[float]


class InsuranceCoverageResult(BaseModel):
    """Output of required_term_coverage()"""
    annual_income: float
    age: int
    dependents: int
    outstanding_loans: float
    required_coverage: float
    method: str = "HLV"
    income_replacement_component: float
    loan_coverage_component: float


class InsuranceAdequacyResult(BaseModel):
    """Output of insurance_adequacy_score()"""
    current_coverage: float
    required_coverage: float
    adequacy_pct: float
    gap: float
    is_adequate: bool
    recommendation: str


class DebtToIncomeResult(BaseModel):
    """Output of debt_to_income_ratio()"""
    total_monthly_debt: float
    monthly_income: float
    dti_ratio: float
    category: str
    recommendation: str


class HealthInsuranceSufficiencyResult(BaseModel):
    """Output of health_insurance_sufficiency()"""
    current_health_cover: float
    recommended_cover: float
    is_sufficient: bool
    gap: float
    recommendation: str


# ============================================================
# MARKET DATA SCHEMAS
# ============================================================

class MarketIndex(BaseModel):
    """Market index data point"""
    name: str
    value: float
    change_pct: float
    timestamp: datetime


class SectorPerformance(BaseModel):
    """Sector performance data"""
    sector: str
    return_1d: float
    return_1w: float
    return_1m: float
    return_1y: float


class MarketSnapshot(BaseModel):
    """Full market snapshot"""
    nifty50: MarketIndex
    india_vix: MarketIndex
    repo_rate: float
    sectors: list[SectorPerformance]
    timestamp: datetime


# ============================================================
# RISK / ML SCHEMAS
# ============================================================

class RiskFactor(BaseModel):
    """Single factor contributing to risk score"""
    feature: str
    impact: float
    direction: str = Field(..., description="'increases_risk' or 'decreases_risk'")


class FinancialStressResult(BaseModel):
    """Output of predict_financial_stress()"""
    score: float = Field(..., ge=0, le=100)
    category: RiskCategory
    top_factors: list[RiskFactor]
    disclaimer: str = "Educational decision support only. Not financial advice."


class UserRiskProfile(BaseModel):
    """Input profile for risk scoring"""
    monthly_income: float
    monthly_expenses: float
    debt_to_income: float
    emergency_months: float
    equity_pct: float
    n_loans: int
    insurance_score: float
    age: int
    n_dependents: int


# ============================================================
# RAG SCHEMAS
# ============================================================

class RAGChunk(BaseModel):
    """Single retrieved chunk"""
    text: str
    source: str
    score: float


class RAGResult(BaseModel):
    """RAG retrieval result"""
    query: str
    chunks: list[RAGChunk]


# ============================================================
# AGENT / ORCHESTRATOR SCHEMAS
# ============================================================

class QuantitativeSummary(BaseModel):
    """Numeric summary grid for DecisionCard"""
    metrics: dict[str, float | str]
    comparison: Optional[NPVComparisonResult] = None
    simulation: Optional[MonteCarloResult] = None
    stress_test: Optional[JobLossStressResult] = None


class DecisionRecommendation(BaseModel):
    """LLM-generated recommendation with citations"""
    headline: str = Field(..., description="One-line strategy recommendation")
    reasoning: str = Field(..., description="Detailed reasoning with cited numbers")
    action_items: list[str]
    confidence: float = Field(..., ge=0, le=1)
    disclaimer: str = "Educational decision support only. Not financial advice."


class DecisionOutput(BaseModel):
    """Final output of the agent orchestrator"""
    user_id: int
    question: str
    question_type: QuestionType
    recommendation: DecisionRecommendation
    quantitative_summary: QuantitativeSummary
    risk_score: Optional[FinancialStressResult] = None
    rag_context: Optional[list[str]] = None
    agent_trace: list[str] = Field(default_factory=list)
    processing_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DecisionRequest(BaseModel):
    """Input to POST /api/decisions/ask"""
    question: str = Field(..., min_length=10, max_length=1000)


class ScopeError(BaseModel):
    """Returned when question is out of scope"""
    question: str
    question_type: QuestionType = QuestionType.OUT_OF_SCOPE
    reason: str
    supported_topics: list[str] = [
        "Loan prepayment vs investment comparison",
        "Rent vs buy analysis",
        "Career break feasibility",
        "SIP planning and optimization",
        "Insurance gap detection",
        "Portfolio stress testing",
    ]
    disclaimer: str = "Educational decision support only. Not financial advice."


# ============================================================
# DECISION LOG SCHEMAS (for DB persistence)
# ============================================================

class DecisionLogCreate(BaseModel):
    question: str
    question_type: QuestionType
    recommendation_headline: str
    recommendation_reasoning: str
    quantitative_summary_json: str
    risk_score: Optional[float] = None
    processing_time_ms: float


class DecisionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    question: str
    question_type: QuestionType
    recommendation_headline: str
    recommendation_reasoning: str
    risk_score: Optional[float]
    processing_time_ms: float
    created_at: datetime


# ============================================================
# SIMULATION RESULT SCHEMAS (for caching)
# ============================================================

class SimulationResultCreate(BaseModel):
    simulation_type: str
    input_params_json: str
    result_json: str
    ttl_seconds: int = 3600


class SimulationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    simulation_type: str
    input_params_json: str
    result_json: str
    created_at: datetime


# ============================================================
# PAGINATION & COMMON
# ============================================================

class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper"""
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


class HealthCheck(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    environment: str = "development"
