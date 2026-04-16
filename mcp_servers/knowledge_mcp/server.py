"""
Knowledge MCP Server — tax rules and insurance clause retrieval.

Initially stubbed with static knowledge. Phase 5 (RAG) replaces with
FAISS + ChromaDB retrieval.
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Knowledge MCP Server", version="1.0.0")

# Static knowledge base — replaced by RAG in Phase 5
TAX_RULES = {
    "80c": {
        "section": "80C",
        "description": "Deductions on investments up to ₹1.5 lakh per year",
        "eligible_instruments": [
            "ELSS Mutual Funds", "PPF", "NSC", "Tax-saving FD (5-year lock-in)",
            "NPS (additional ₹50K under 80CCD(1B))", "Life Insurance Premium",
            "Tuition Fees", "Home Loan Principal Repayment",
        ],
        "max_deduction": 150000,
        "notes": "Combined limit for all 80C instruments.",
    },
    "80d": {
        "section": "80D",
        "description": "Deductions on health insurance premiums",
        "limits": {
            "self_family": 25000,
            "self_family_senior": 50000,
            "parents": 25000,
            "parents_senior": 50000,
        },
        "max_deduction": 100000,
        "notes": "Includes preventive health check-up up to ₹5,000.",
    },
    "24b": {
        "section": "24(b)",
        "description": "Deduction on home loan interest",
        "max_deduction_self_occupied": 200000,
        "max_deduction_let_out": "No limit (actual interest)",
        "notes": "Applies to interest component of home loan EMI.",
    },
    "10_14": {
        "section": "10(14)",
        "description": "HRA exemption from salary",
        "calculation": "Minimum of: actual HRA, 50% of salary (metro) / 40% (non-metro), rent paid - 10% of salary",
        "notes": "Only if living in rented accommodation.",
    },
}

INSURANCE_GUIDELINES = {
    "term_insurance": {
        "topic": "Term Insurance Selection",
        "guidelines": [
            "Cover should be 10-15x annual income",
            "Pure term plans are most cost-effective",
            "Claim settlement ratio > 95% is recommended",
            "Choose policy till age 60-65",
            "Add critical illness rider if employer doesn't cover",
        ],
    },
    "health_insurance": {
        "topic": "Health Insurance",
        "guidelines": [
            "Minimum ₹10L cover for metro cities",
            "Choose plans with no co-payment clause",
            "Check sub-limits on room rent",
            "Pre-existing disease waiting period: usually 2-4 years",
            "Restoration benefit is important for family floater plans",
        ],
    },
}

TOOLS = {
    "retrieve_tax_rules": {
        "description": "Retrieve Indian tax rules and deduction information",
        "parameters": {
            "query": {"type": "string", "description": "Tax-related query"},
        },
        "required": ["query"],
    },
    "retrieve_insurance_clause": {
        "description": "Retrieve insurance guidelines and policy clauses",
        "parameters": {
            "user_id": {"type": "integer", "description": "User ID for user-specific policies"},
            "query": {"type": "string", "description": "Insurance-related query"},
        },
        "required": ["query"],
    },
}


def _search_tax_rules(query: str) -> dict:
    """Search static tax rules based on query keywords."""
    query_lower = query.lower()
    results = []

    for key, rule in TAX_RULES.items():
        text = f"{rule.get('section', '')} {rule.get('description', '')} {rule.get('notes', '')}".lower()
        if any(word in text for word in query_lower.split()):
            results.append(rule)

    # If no matches, return all rules
    if not results:
        results = list(TAX_RULES.values())

    return {
        "query": query,
        "results": results[:5],
        "source": "static_knowledge_base",
        "note": "Will be replaced by RAG retrieval in Phase 5",
    }


def _search_insurance(user_id: int | None, query: str) -> dict:
    """Search insurance guidelines."""
    query_lower = query.lower()
    results = []

    for key, guideline in INSURANCE_GUIDELINES.items():
        text = f"{guideline.get('topic', '')} {' '.join(guideline.get('guidelines', []))}".lower()
        if any(word in text for word in query_lower.split()):
            results.append(guideline)

    if not results:
        results = list(INSURANCE_GUIDELINES.values())

    return {
        "query": query,
        "user_id": user_id,
        "results": results,
        "source": "static_knowledge_base",
        "note": "User-specific policy retrieval via ChromaDB coming in Phase 5",
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
        if request.tool_name == "retrieve_tax_rules":
            result = _search_tax_rules(request.arguments.get("query", ""))
        elif request.tool_name == "retrieve_insurance_clause":
            result = _search_insurance(
                request.arguments.get("user_id"),
                request.arguments.get("query", ""),
            )
        else:
            return ToolCallResponse(
                tool_name=request.tool_name, result={},
                error=f"Unknown tool: {request.tool_name}",
            )
        return ToolCallResponse(tool_name=request.tool_name, result=result)
    except Exception as e:
        return ToolCallResponse(tool_name=request.tool_name, result={}, error=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8015)
