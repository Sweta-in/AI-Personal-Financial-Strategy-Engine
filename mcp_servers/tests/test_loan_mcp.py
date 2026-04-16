"""
MCP Server integration tests — verifies tool call/response contracts.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from httpx import AsyncClient, ASGITransport


# --- Loan MCP ---

@pytest.mark.asyncio
async def test_loan_mcp_list_tools():
    from mcp_servers.loan_mcp.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/tools")
        assert resp.status_code == 200
        tools = resp.json()["tools"]
        assert "calculate_emi" in tools
        assert "prepayment_benefit" in tools


@pytest.mark.asyncio
async def test_loan_mcp_calculate_emi():
    from mcp_servers.loan_mcp.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/call", json={
            "tool_name": "calculate_emi",
            "arguments": {"principal": 3000000, "annual_rate": 8.5, "tenure_months": 240},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["error"] is None
        assert abs(data["result"]["monthly_emi"] - 26049) < 50


@pytest.mark.asyncio
async def test_loan_mcp_prepayment():
    from mcp_servers.loan_mcp.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/call", json={
            "tool_name": "prepayment_benefit",
            "arguments": {
                "outstanding": 2500000,
                "annual_rate": 8.5,
                "remaining_months": 200,
                "prepayment_amount": 500000,
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["error"] is None
        assert data["result"]["interest_saved"] > 0
        assert data["result"]["months_reduced"] > 0


@pytest.mark.asyncio
async def test_loan_mcp_dti():
    from mcp_servers.loan_mcp.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/call", json={
            "tool_name": "debt_to_income_ratio",
            "arguments": {"total_monthly_debt": 30000, "monthly_income": 100000},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"]["category"] == "Manageable"


@pytest.mark.asyncio
async def test_loan_mcp_unknown_tool():
    from mcp_servers.loan_mcp.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/call", json={
            "tool_name": "nonexistent",
            "arguments": {},
        })
        data = resp.json()
        assert data["error"] is not None
