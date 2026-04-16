"""
MCP Client — calls MCP servers via HTTP.

Each MCP server exposes /tools (list) and /call (execute).
This client provides a unified interface for the orchestrator.
"""

from __future__ import annotations

import httpx
from loguru import logger


# MCP Server endpoints — configurable via env in production
MCP_SERVERS = {
    "loan": "http://localhost:8010",
    "portfolio": "http://localhost:8011",
    "insurance": "http://localhost:8012",
    "market": "http://localhost:8013",
    "risk": "http://localhost:8014",
    "knowledge": "http://localhost:8015",
}


async def list_tools(server_name: str) -> dict:
    """List available tools from an MCP server."""
    url = f"{MCP_SERVERS[server_name]}/tools"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


async def call_tool(server_name: str, tool_name: str, arguments: dict) -> dict:
    """
    Call a tool on the specified MCP server.

    Args:
        server_name: Key from MCP_SERVERS (loan, portfolio, etc.)
        tool_name: Name of the tool to call
        arguments: Tool arguments as dict

    Returns:
        Tool result dict or error dict
    """
    url = f"{MCP_SERVERS[server_name]}/call"
    payload = {"tool_name": tool_name, "arguments": arguments}

    logger.info(f"MCP call: {server_name}/{tool_name} with {list(arguments.keys())}")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            result = resp.json()

            if result.get("error"):
                logger.error(f"MCP error: {server_name}/{tool_name}: {result['error']}")
                return {"error": result["error"]}

            logger.info(f"MCP success: {server_name}/{tool_name}")
            return result.get("result", {})

    except httpx.ConnectError:
        logger.warning(f"MCP server {server_name} not reachable — using direct call fallback")
        return await _direct_call_fallback(server_name, tool_name, arguments)
    except Exception as e:
        logger.error(f"MCP call failed: {server_name}/{tool_name}: {e}")
        return {"error": str(e)}


async def _direct_call_fallback(server_name: str, tool_name: str, arguments: dict) -> dict:
    """
    Fallback: call quant functions directly when MCP servers aren't running.
    This enables local development without Docker Compose.
    """
    try:
        if server_name == "loan":
            from quant.loan_engine import (
                build_amortization_schedule,
                calculate_emi,
                calculate_prepayment_benefit,
                debt_to_income_ratio,
                refinance_break_even,
            )
            funcs = {
                "calculate_emi": calculate_emi,
                "amortization_schedule": build_amortization_schedule,
                "prepayment_benefit": calculate_prepayment_benefit,
                "refinance_break_even": refinance_break_even,
                "debt_to_income_ratio": debt_to_income_ratio,
            }
        elif server_name == "portfolio":
            from quant.portfolio_engine import (
                calculate_max_drawdown,
                calculate_sharpe_ratio,
                calculate_var,
                net_worth,
            )
            from quant.simulation_engine import job_loss_stress_test, monte_carlo_portfolio_growth
            funcs = {
                "monte_carlo_simulate": monte_carlo_portfolio_growth,
                "calculate_sharpe_ratio": calculate_sharpe_ratio,
                "calculate_max_drawdown": calculate_max_drawdown,
                "calculate_var": calculate_var,
                "net_worth": net_worth,
                "job_loss_stress_test": job_loss_stress_test,
            }
        elif server_name == "insurance":
            from quant.insurance_engine import (
                health_insurance_sufficiency,
                insurance_adequacy_score,
                required_term_coverage,
            )
            funcs = {
                "required_term_coverage": required_term_coverage,
                "insurance_adequacy_score": insurance_adequacy_score,
                "health_insurance_sufficiency": health_insurance_sufficiency,
            }
        elif server_name == "risk":
            from mcp_servers.risk_mcp.server import _rule_based_stress
            funcs = {"predict_financial_stress": _rule_based_stress}
        elif server_name == "knowledge":
            from mcp_servers.knowledge_mcp.server import _search_tax_rules, _search_insurance
            funcs = {
                "retrieve_tax_rules": lambda query: _search_tax_rules(query),
                "retrieve_insurance_clause": lambda user_id=None, query="": _search_insurance(user_id, query),
            }
        elif server_name == "market":
            from mcp_servers.market_mcp.server import _get_yfinance_data
            from datetime import datetime
            funcs = {
                "get_nifty50": lambda: _get_yfinance_data("^NSEI"),
                "get_india_vix": lambda: _get_yfinance_data("^INDIAVIX"),
                "get_repo_rate": lambda: {"repo_rate": 6.50, "timestamp": datetime.utcnow().isoformat()},
            }
        else:
            return {"error": f"Unknown server: {server_name}"}

        if tool_name not in funcs:
            return {"error": f"Unknown tool: {tool_name}"}

        result = funcs[tool_name](**arguments)
        if hasattr(result, "model_dump"):
            return result.model_dump()
        return result

    except Exception as e:
        logger.error(f"Direct fallback failed: {server_name}/{tool_name}: {e}")
        return {"error": str(e)}
