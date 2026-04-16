"""
Loan MCP Server — exposes loan quant functions as MCP tools.

Tools: calculate_emi, amortization_schedule, prepayment_benefit,
       refinance_break_even, debt_to_income_ratio
"""

from __future__ import annotations

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI
from pydantic import BaseModel

from quant.loan_engine import (
    build_amortization_schedule,
    calculate_emi,
    calculate_prepayment_benefit,
    debt_to_income_ratio,
    refinance_break_even,
)

app = FastAPI(title="Loan MCP Server", version="1.0.0")

# ============================================================
# Tool Registry
# ============================================================

TOOLS = {
    "calculate_emi": {
        "description": "Calculate EMI for a loan using reducing-balance formula",
        "parameters": {
            "principal": {"type": "number", "description": "Loan principal amount"},
            "annual_rate": {"type": "number", "description": "Annual interest rate (%)"},
            "tenure_months": {"type": "integer", "description": "Loan tenure in months"},
        },
        "required": ["principal", "annual_rate", "tenure_months"],
    },
    "amortization_schedule": {
        "description": "Generate month-by-month amortization schedule",
        "parameters": {
            "principal": {"type": "number", "description": "Loan principal amount"},
            "annual_rate": {"type": "number", "description": "Annual interest rate (%)"},
            "tenure_months": {"type": "integer", "description": "Loan tenure in months"},
        },
        "required": ["principal", "annual_rate", "tenure_months"],
    },
    "prepayment_benefit": {
        "description": "Calculate benefit of making a lump-sum loan prepayment",
        "parameters": {
            "outstanding": {"type": "number", "description": "Outstanding balance"},
            "annual_rate": {"type": "number", "description": "Annual interest rate (%)"},
            "remaining_months": {"type": "integer", "description": "Remaining tenure in months"},
            "prepayment_amount": {"type": "number", "description": "Prepayment amount"},
        },
        "required": ["outstanding", "annual_rate", "remaining_months", "prepayment_amount"],
    },
    "refinance_break_even": {
        "description": "Calculate when refinancing breaks even after processing fee",
        "parameters": {
            "old_rate": {"type": "number", "description": "Current annual rate (%)"},
            "new_rate": {"type": "number", "description": "New annual rate (%)"},
            "outstanding": {"type": "number", "description": "Outstanding balance"},
            "remaining_months": {"type": "integer", "description": "Remaining tenure"},
            "processing_fee": {"type": "number", "description": "Processing fee"},
        },
        "required": ["old_rate", "new_rate", "outstanding", "remaining_months", "processing_fee"],
    },
    "debt_to_income_ratio": {
        "description": "Calculate debt-to-income ratio and categorize financial health",
        "parameters": {
            "total_monthly_debt": {"type": "number", "description": "Total monthly debt payments"},
            "monthly_income": {"type": "number", "description": "Gross monthly income"},
        },
        "required": ["total_monthly_debt", "monthly_income"],
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
    """List all available tools."""
    return {"tools": TOOLS}


@app.post("/call", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest):
    """Call a tool with the given arguments."""
    try:
        if request.tool_name == "calculate_emi":
            result = calculate_emi(**request.arguments)
        elif request.tool_name == "amortization_schedule":
            result = build_amortization_schedule(**request.arguments)
        elif request.tool_name == "prepayment_benefit":
            result = calculate_prepayment_benefit(**request.arguments)
        elif request.tool_name == "refinance_break_even":
            result = refinance_break_even(**request.arguments)
        elif request.tool_name == "debt_to_income_ratio":
            result = debt_to_income_ratio(**request.arguments)
        else:
            return ToolCallResponse(
                tool_name=request.tool_name,
                result={},
                error=f"Unknown tool: {request.tool_name}",
            )

        return ToolCallResponse(
            tool_name=request.tool_name,
            result=result.model_dump(),
        )
    except Exception as e:
        return ToolCallResponse(
            tool_name=request.tool_name,
            result={},
            error=str(e),
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
