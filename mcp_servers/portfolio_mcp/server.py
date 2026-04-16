"""
Portfolio MCP Server — Monte Carlo, Sharpe, drawdown, VaR, net worth, stress test.
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI
from pydantic import BaseModel

from quant.portfolio_engine import (
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_var,
    net_worth,
)
from quant.simulation_engine import job_loss_stress_test, monte_carlo_portfolio_growth

app = FastAPI(title="Portfolio MCP Server", version="1.0.0")

TOOLS = {
    "monte_carlo_simulate": {
        "description": "Run Monte Carlo portfolio growth simulation with P10/P50/P90",
        "parameters": {
            "initial_value": {"type": "number"},
            "monthly_sip": {"type": "number"},
            "annual_return_mean": {"type": "number"},
            "annual_return_std": {"type": "number"},
            "time_horizon_months": {"type": "integer"},
            "n_simulations": {"type": "integer", "default": 10000},
        },
        "required": ["initial_value", "monthly_sip", "annual_return_mean", "annual_return_std", "time_horizon_months"],
    },
    "calculate_sharpe_ratio": {
        "description": "Calculate annualized Sharpe ratio from monthly returns",
        "parameters": {
            "returns": {"type": "array", "items": {"type": "number"}},
            "risk_free_rate": {"type": "number", "default": 0.065},
        },
        "required": ["returns"],
    },
    "calculate_max_drawdown": {
        "description": "Calculate maximum peak-to-trough drawdown",
        "parameters": {
            "portfolio_values": {"type": "array", "items": {"type": "number"}},
        },
        "required": ["portfolio_values"],
    },
    "calculate_var": {
        "description": "Calculate parametric Value at Risk",
        "parameters": {
            "returns": {"type": "array", "items": {"type": "number"}},
            "confidence": {"type": "number", "default": 0.95},
        },
        "required": ["returns"],
    },
    "net_worth": {
        "description": "Calculate net worth from assets and liabilities",
        "parameters": {
            "assets": {"type": "object"},
            "liabilities": {"type": "object"},
        },
        "required": ["assets", "liabilities"],
    },
    "job_loss_stress_test": {
        "description": "Stress test financial survival during income loss",
        "parameters": {
            "monthly_expenses": {"type": "number"},
            "emergency_fund": {"type": "number"},
            "income_loss_months": {"type": "integer"},
            "additional_income": {"type": "number", "default": 0},
        },
        "required": ["monthly_expenses", "emergency_fund", "income_loss_months"],
    },
}


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
        name = request.tool_name
        args = request.arguments

        if name == "monte_carlo_simulate":
            result = monte_carlo_portfolio_growth(**args)
        elif name == "calculate_sharpe_ratio":
            result = calculate_sharpe_ratio(**args)
        elif name == "calculate_max_drawdown":
            result = calculate_max_drawdown(**args)
        elif name == "calculate_var":
            result = calculate_var(**args)
        elif name == "net_worth":
            result = net_worth(**args)
        elif name == "job_loss_stress_test":
            result = job_loss_stress_test(**args)
        else:
            return ToolCallResponse(tool_name=name, result={}, error=f"Unknown tool: {name}")

        return ToolCallResponse(tool_name=name, result=result.model_dump())
    except Exception as e:
        return ToolCallResponse(tool_name=request.tool_name, result={}, error=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)
