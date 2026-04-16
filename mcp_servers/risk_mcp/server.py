"""
Risk MCP Server — financial stress prediction.

Initially rule-based. Phase 6 replaces with XGBoost + SHAP.
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI
from pydantic import BaseModel

from backend.app.schemas.models import FinancialStressResult, RiskCategory, RiskFactor

app = FastAPI(title="Risk MCP Server", version="1.0.0")

TOOLS = {
    "predict_financial_stress": {
        "description": "Predict financial stress score (0-100) with top contributing factors",
        "parameters": {
            "monthly_income": {"type": "number"},
            "monthly_expenses": {"type": "number"},
            "debt_to_income": {"type": "number"},
            "emergency_months": {"type": "number"},
            "equity_pct": {"type": "number"},
            "n_loans": {"type": "integer"},
            "insurance_score": {"type": "number"},
            "age": {"type": "integer"},
            "n_dependents": {"type": "integer"},
        },
        "required": ["monthly_income", "monthly_expenses", "debt_to_income",
                      "emergency_months", "equity_pct", "n_loans",
                      "insurance_score", "age", "n_dependents"],
    },
}


def _rule_based_stress(
    monthly_income: float,
    monthly_expenses: float,
    debt_to_income: float,
    emergency_months: float,
    equity_pct: float,
    n_loans: int,
    insurance_score: float,
    age: int,
    n_dependents: int,
) -> FinancialStressResult:
    """
    Rule-based financial stress scoring.
    Score 0 = no stress, 100 = maximum stress.

    Factors and weights:
    - DTI ratio: 25 points max (>0.5 = 25, >0.36 = 15, >0.2 = 5)
    - Emergency fund: 25 points max (<1mo = 25, <3mo = 15, <6mo = 5)
    - Savings rate: 15 points max (negative = 15, <10% = 10, <20% = 5)
    - Insurance gap: 15 points max (<50% = 15, <80% = 8, <100% = 3)
    - Loan count: 10 points max (>4 = 10, >2 = 5)
    - Equity concentration: 10 points max (>80% = 10, >60% = 5)
    """
    score = 0.0
    factors = []

    # 1. DTI ratio (25 pts)
    if debt_to_income > 0.50:
        score += 25
        factors.append(RiskFactor(feature="debt_to_income", impact=25.0, direction="increases_risk"))
    elif debt_to_income > 0.36:
        score += 15
        factors.append(RiskFactor(feature="debt_to_income", impact=15.0, direction="increases_risk"))
    elif debt_to_income > 0.20:
        score += 5
        factors.append(RiskFactor(feature="debt_to_income", impact=5.0, direction="increases_risk"))

    # 2. Emergency fund (25 pts)
    if emergency_months < 1:
        score += 25
        factors.append(RiskFactor(feature="emergency_months", impact=25.0, direction="increases_risk"))
    elif emergency_months < 3:
        score += 15
        factors.append(RiskFactor(feature="emergency_months", impact=15.0, direction="increases_risk"))
    elif emergency_months < 6:
        score += 5
        factors.append(RiskFactor(feature="emergency_months", impact=5.0, direction="increases_risk"))

    # 3. Savings rate (15 pts)
    savings_rate = (monthly_income - monthly_expenses) / monthly_income if monthly_income > 0 else 0
    if savings_rate < 0:
        score += 15
        factors.append(RiskFactor(feature="savings_rate", impact=15.0, direction="increases_risk"))
    elif savings_rate < 0.10:
        score += 10
        factors.append(RiskFactor(feature="savings_rate", impact=10.0, direction="increases_risk"))
    elif savings_rate < 0.20:
        score += 5
        factors.append(RiskFactor(feature="savings_rate", impact=5.0, direction="increases_risk"))

    # 4. Insurance gap (15 pts)
    if insurance_score < 0.50:
        score += 15
        factors.append(RiskFactor(feature="insurance_score", impact=15.0, direction="increases_risk"))
    elif insurance_score < 0.80:
        score += 8
        factors.append(RiskFactor(feature="insurance_score", impact=8.0, direction="increases_risk"))
    elif insurance_score < 1.0:
        score += 3
        factors.append(RiskFactor(feature="insurance_score", impact=3.0, direction="increases_risk"))

    # 5. Loan count (10 pts)
    if n_loans > 4:
        score += 10
        factors.append(RiskFactor(feature="n_loans", impact=10.0, direction="increases_risk"))
    elif n_loans > 2:
        score += 5
        factors.append(RiskFactor(feature="n_loans", impact=5.0, direction="increases_risk"))

    # 6. Equity concentration (10 pts)
    if equity_pct > 0.80:
        score += 10
        factors.append(RiskFactor(feature="equity_pct", impact=10.0, direction="increases_risk"))
    elif equity_pct > 0.60:
        score += 5
        factors.append(RiskFactor(feature="equity_pct", impact=5.0, direction="increases_risk"))

    # Categorize
    score = min(100, max(0, score))
    if score <= 30:
        category = RiskCategory.LOW
    elif score <= 60:
        category = RiskCategory.MEDIUM
    else:
        category = RiskCategory.HIGH

    # Top 3 factors
    factors.sort(key=lambda f: f.impact, reverse=True)
    top_factors = factors[:3]

    return FinancialStressResult(
        score=score,
        category=category,
        top_factors=top_factors,
    )


class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: dict


class ToolCallResponse(BaseModel):
    tool_name: str
    result: dict
    error: str | None = None


@app.get("/tools")
async def list_tools():
    return {"tools": TOOLS}


@app.post("/call", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest):
    try:
        if request.tool_name == "predict_financial_stress":
            result = _rule_based_stress(**request.arguments)
            return ToolCallResponse(tool_name=request.tool_name, result=result.model_dump())
        else:
            return ToolCallResponse(
                tool_name=request.tool_name, result={},
                error=f"Unknown tool: {request.tool_name}",
            )
    except Exception as e:
        return ToolCallResponse(tool_name=request.tool_name, result={}, error=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8014)
