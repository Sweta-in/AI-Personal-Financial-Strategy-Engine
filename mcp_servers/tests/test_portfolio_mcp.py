"""
Portfolio and Insurance MCP integration tests.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from httpx import AsyncClient, ASGITransport


# --- Portfolio MCP ---

@pytest.mark.asyncio
async def test_portfolio_mcp_monte_carlo():
    from mcp_servers.portfolio_mcp.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/call", json={
            "tool_name": "monte_carlo_simulate",
            "arguments": {
                "initial_value": 1000000,
                "monthly_sip": 25000,
                "annual_return_mean": 0.12,
                "annual_return_std": 0.18,
                "time_horizon_months": 60,
                "n_simulations": 100,
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["error"] is None
        assert data["result"]["final_value"]["p50"] > 0


@pytest.mark.asyncio
async def test_portfolio_mcp_net_worth():
    from mcp_servers.portfolio_mcp.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/call", json={
            "tool_name": "net_worth",
            "arguments": {
                "assets": {"equity": 2000000, "fd": 500000},
                "liabilities": {"home_loan": 1500000},
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"]["net_worth"] == 1000000


@pytest.mark.asyncio
async def test_portfolio_mcp_stress_test():
    from mcp_servers.portfolio_mcp.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/call", json={
            "tool_name": "job_loss_stress_test",
            "arguments": {
                "monthly_expenses": 50000,
                "emergency_fund": 300000,
                "income_loss_months": 6,
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"]["survives"] is True


# --- Insurance MCP ---

@pytest.mark.asyncio
async def test_insurance_mcp_coverage():
    from mcp_servers.insurance_mcp.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/call", json={
            "tool_name": "required_term_coverage",
            "arguments": {
                "annual_income": 1200000,
                "age": 30,
                "dependents": 2,
                "outstanding_loans": 3000000,
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["error"] is None
        assert data["result"]["required_coverage"] > 10000000


@pytest.mark.asyncio
async def test_insurance_mcp_adequacy():
    from mcp_servers.insurance_mcp.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/call", json={
            "tool_name": "insurance_adequacy_score",
            "arguments": {"current_coverage": 5000000, "required_coverage": 10000000},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"]["is_adequate"] is False
