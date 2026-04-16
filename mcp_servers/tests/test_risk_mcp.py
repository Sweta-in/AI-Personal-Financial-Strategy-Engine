"""
Risk and Knowledge MCP integration tests.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_risk_mcp_low_stress():
    from mcp_servers.risk_mcp.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/call", json={
            "tool_name": "predict_financial_stress",
            "arguments": {
                "monthly_income": 200000,
                "monthly_expenses": 80000,
                "debt_to_income": 0.15,
                "emergency_months": 12,
                "equity_pct": 0.40,
                "n_loans": 1,
                "insurance_score": 1.0,
                "age": 30,
                "n_dependents": 1,
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["error"] is None
        assert data["result"]["category"] == "low"


@pytest.mark.asyncio
async def test_risk_mcp_high_stress():
    from mcp_servers.risk_mcp.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/call", json={
            "tool_name": "predict_financial_stress",
            "arguments": {
                "monthly_income": 50000,
                "monthly_expenses": 55000,
                "debt_to_income": 0.60,
                "emergency_months": 0.5,
                "equity_pct": 0.90,
                "n_loans": 5,
                "insurance_score": 0.3,
                "age": 45,
                "n_dependents": 3,
            },
        })
        data = resp.json()
        assert data["result"]["score"] >= 60
        assert data["result"]["category"] == "high"
        assert len(data["result"]["top_factors"]) == 3


@pytest.mark.asyncio
async def test_knowledge_mcp_tax_rules():
    from mcp_servers.knowledge_mcp.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/call", json={
            "tool_name": "retrieve_tax_rules",
            "arguments": {"query": "home loan interest deduction"},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["error"] is None
        assert len(data["result"]["results"]) > 0


@pytest.mark.asyncio
async def test_knowledge_mcp_insurance():
    from mcp_servers.knowledge_mcp.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/call", json={
            "tool_name": "retrieve_insurance_clause",
            "arguments": {"query": "term insurance coverage", "user_id": 1},
        })
        data = resp.json()
        assert data["error"] is None
        assert len(data["result"]["results"]) > 0


@pytest.mark.asyncio
async def test_market_mcp_nifty():
    from mcp_servers.market_mcp.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/call", json={
            "tool_name": "get_nifty50",
            "arguments": {},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "value" in data["result"]


@pytest.mark.asyncio
async def test_market_mcp_repo_rate():
    from mcp_servers.market_mcp.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/call", json={
            "tool_name": "get_repo_rate",
            "arguments": {},
        })
        data = resp.json()
        assert data["result"]["repo_rate"] == 6.5
