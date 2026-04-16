"""
Insurance MCP Server — term coverage, adequacy score, health sufficiency.
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI
from pydantic import BaseModel

from quant.insurance_engine import (
    health_insurance_sufficiency,
    insurance_adequacy_score,
    required_term_coverage,
)

app = FastAPI(title="Insurance MCP Server", version="1.0.0")

TOOLS = {
    "required_term_coverage": {
        "description": "Calculate required term insurance using HLV method",
        "parameters": {
            "annual_income": {"type": "number"},
            "age": {"type": "integer"},
            "dependents": {"type": "integer"},
            "outstanding_loans": {"type": "number"},
        },
        "required": ["annual_income", "age", "dependents", "outstanding_loans"],
    },
    "insurance_adequacy_score": {
        "description": "Score insurance adequacy as percentage of requirement",
        "parameters": {
            "current_coverage": {"type": "number"},
            "required_coverage": {"type": "number"},
        },
        "required": ["current_coverage", "required_coverage"],
    },
    "health_insurance_sufficiency": {
        "description": "Assess health insurance coverage sufficiency",
        "parameters": {
            "current_health_cover": {"type": "number"},
            "age": {"type": "integer"},
            "dependents": {"type": "integer"},
            "city_tier": {"type": "integer", "default": 1},
        },
        "required": ["current_health_cover", "age", "dependents"],
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

        if name == "required_term_coverage":
            result = required_term_coverage(**args)
        elif name == "insurance_adequacy_score":
            result = insurance_adequacy_score(**args)
        elif name == "health_insurance_sufficiency":
            result = health_insurance_sufficiency(**args)
        else:
            return ToolCallResponse(tool_name=name, result={}, error=f"Unknown tool: {name}")

        return ToolCallResponse(tool_name=name, result=result.model_dump())
    except Exception as e:
        return ToolCallResponse(tool_name=request.tool_name, result={}, error=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8012)
