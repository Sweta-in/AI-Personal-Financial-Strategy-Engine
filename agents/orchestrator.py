"""
LangGraph Orchestrator — multi-agent financial decision pipeline.

StateGraph nodes:
1. classify_question → LLM classifies question type
2. load_user_profile → fetch from DB
3. execute_tools → call MCP servers based on question_type
4. retrieve_context → call KnowledgeMCP for regulation knowledge
5. score_risk → call RiskMCP
6. generate_recommendation → LLM interprets tool outputs
7. format_output → assemble DecisionOutput

LLM: Groq API (llama3-8b-8192), Temperature=0.1
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from typing import TypedDict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from loguru import logger

from backend.app.schemas.models import (
    DecisionOutput,
    DecisionRecommendation,
    FinancialStressResult,
    MonteCarloResult,
    QuantitativeSummary,
    QuestionType,
    RiskCategory,
    RiskFactor,
    ScopeError,
)
from agents.mcp_client import call_tool
from agents.prompts import (
    CLASSIFICATION_SYSTEM_PROMPT,
    CLASSIFICATION_USER_TEMPLATE,
    RECOMMENDATION_SYSTEM_PROMPT,
    RECOMMENDATION_USER_TEMPLATE,
)


# ============================================================
# Agent State
# ============================================================

class AgentState(TypedDict, total=False):
    user_id: int
    question: str
    question_type: str
    user_profile: dict
    tool_results: dict
    rag_context: list[str]
    risk_score: dict
    recommendation: dict
    quantitative_summary: dict
    agent_trace: list[str]
    error: str | None
    start_time: float


# ============================================================
# LLM Helper
# ============================================================

async def _call_llm(system_prompt: str, user_message: str) -> str:
    """Call Groq LLM (or fallback to rule-based for local dev)."""
    groq_key = os.environ.get("GROQ_API_KEY", "")
    model = os.environ.get("GROQ_MODEL", "llama3-8b-8192")

    if groq_key and groq_key != "your-groq-api-key":
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message},
                        ],
                        "temperature": 0.1,
                        "max_tokens": 2048,
                    },
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"Groq API call failed: {e} — falling back to rule-based")

    # Fallback: rule-based classification/recommendation
    return ""


# ============================================================
# Node Functions
# ============================================================

async def classify_question(state: AgentState) -> AgentState:
    """Node 1: Classify the user's question type."""
    state["agent_trace"] = state.get("agent_trace", [])
    state["agent_trace"].append("classify_question")
    state["start_time"] = time.time()

    question = state["question"]

    # Try LLM classification
    user_msg = CLASSIFICATION_USER_TEMPLATE.format(question=question)
    llm_result = await _call_llm(CLASSIFICATION_SYSTEM_PROMPT, user_msg)

    # Parse classification
    q_lower = question.lower()
    llm_lower = llm_result.strip().lower() if llm_result else ""

    # Hard-coded out-of-scope patterns
    out_of_scope_patterns = [
        "which stock", "buy stock", "sell stock", "will market crash",
        "stock recommendation", "best stock", "crypto", "bitcoin",
    ]
    if any(p in q_lower for p in out_of_scope_patterns):
        state["question_type"] = QuestionType.OUT_OF_SCOPE
        return state

    # Use LLM result if valid
    type_map = {
        "loan_decision": QuestionType.LOAN_DECISION,
        "portfolio_risk": QuestionType.PORTFOLIO_RISK,
        "insurance_gap": QuestionType.INSURANCE_GAP,
        "scenario_planning": QuestionType.SCENARIO_PLANNING,
        "market_context": QuestionType.MARKET_CONTEXT,
        "out_of_scope": QuestionType.OUT_OF_SCOPE,
    }

    if llm_lower in type_map:
        state["question_type"] = type_map[llm_lower]
    else:
        # Keyword fallback
        if any(w in q_lower for w in ["loan", "emi", "prepay", "refinanc", "rent", "buy house"]):
            state["question_type"] = QuestionType.LOAN_DECISION
        elif any(w in q_lower for w in ["portfolio", "invest", "sip", "mutual fund", "return", "drawdown"]):
            state["question_type"] = QuestionType.PORTFOLIO_RISK
        elif any(w in q_lower for w in ["insurance", "cover", "term plan", "health"]):
            state["question_type"] = QuestionType.INSURANCE_GAP
        elif any(w in q_lower for w in ["career break", "job loss", "what if", "scenario", "stress"]):
            state["question_type"] = QuestionType.SCENARIO_PLANNING
        elif any(w in q_lower for w in ["nifty", "market", "vix", "repo rate", "sector"]):
            state["question_type"] = QuestionType.MARKET_CONTEXT
        else:
            state["question_type"] = QuestionType.LOAN_DECISION  # Default

    logger.info(f"Classified question as: {state['question_type']}")
    return state


async def load_user_profile(state: AgentState) -> AgentState:
    """Node 2: Load user's financial profile from DB."""
    state["agent_trace"].append("load_user_profile")

    # In production, this queries the database via the backend API
    # For now, use a default profile if not provided
    if not state.get("user_profile"):
        state["user_profile"] = {
            "user_id": state["user_id"],
            "monthly_income": 150000,
            "monthly_expenses": 80000,
            "age": 32,
            "dependents": 2,
            "loans": [],
            "assets": [],
            "insurance_policies": [],
        }

    return state


async def execute_tools(state: AgentState) -> AgentState:
    """Node 3: Call appropriate MCP servers based on question_type."""
    state["agent_trace"].append("execute_tools")
    state["tool_results"] = {}

    question_type = state["question_type"]
    profile = state.get("user_profile", {})

    try:
        if question_type == QuestionType.LOAN_DECISION:
            # Loan analysis + NPV comparison
            emi_result = await call_tool("loan", "calculate_emi", {
                "principal": 3000000,
                "annual_rate": 8.5,
                "tenure_months": 240,
            })
            state["tool_results"]["emi"] = emi_result

            prepayment_result = await call_tool("loan", "prepayment_benefit", {
                "outstanding": 2500000,
                "annual_rate": 8.5,
                "remaining_months": 200,
                "prepayment_amount": 500000,
            })
            state["tool_results"]["prepayment"] = prepayment_result

            mc_result = await call_tool("portfolio", "monte_carlo_simulate", {
                "initial_value": 500000,
                "monthly_sip": 0,
                "annual_return_mean": 0.12,
                "annual_return_std": 0.18,
                "time_horizon_months": 200,
                "n_simulations": 10000,
            })
            state["tool_results"]["monte_carlo"] = mc_result

        elif question_type == QuestionType.PORTFOLIO_RISK:
            mc_result = await call_tool("portfolio", "monte_carlo_simulate", {
                "initial_value": 1000000,
                "monthly_sip": 25000,
                "annual_return_mean": 0.12,
                "annual_return_std": 0.18,
                "time_horizon_months": 120,
                "n_simulations": 10000,
            })
            state["tool_results"]["monte_carlo"] = mc_result

            market = await call_tool("market", "get_nifty50", {})
            state["tool_results"]["nifty50"] = market

            vix = await call_tool("market", "get_india_vix", {})
            state["tool_results"]["india_vix"] = vix

        elif question_type == QuestionType.INSURANCE_GAP:
            coverage = await call_tool("insurance", "required_term_coverage", {
                "annual_income": profile.get("monthly_income", 150000) * 12,
                "age": profile.get("age", 30),
                "dependents": profile.get("dependents", 2),
                "outstanding_loans": 3000000,
            })
            state["tool_results"]["required_coverage"] = coverage

            total_cover = sum(
                p.get("sum_assured", 0)
                for p in profile.get("insurance_policies", [])
            ) or 5000000

            adequacy = await call_tool("insurance", "insurance_adequacy_score", {
                "current_coverage": total_cover,
                "required_coverage": coverage.get("required_coverage", 10000000),
            })
            state["tool_results"]["adequacy"] = adequacy

        elif question_type == QuestionType.SCENARIO_PLANNING:
            stress = await call_tool("portfolio", "job_loss_stress_test", {
                "monthly_expenses": profile.get("monthly_expenses", 80000),
                "emergency_fund": 500000,
                "income_loss_months": 6,
            })
            state["tool_results"]["stress_test"] = stress

            mc_crash = await call_tool("portfolio", "monte_carlo_simulate", {
                "initial_value": 1000000,
                "monthly_sip": 0,
                "annual_return_mean": -0.15,
                "annual_return_std": 0.30,
                "time_horizon_months": 12,
                "n_simulations": 10000,
            })
            state["tool_results"]["crash_simulation"] = mc_crash

        elif question_type == QuestionType.MARKET_CONTEXT:
            nifty = await call_tool("market", "get_nifty50", {})
            state["tool_results"]["nifty50"] = nifty

            vix = await call_tool("market", "get_india_vix", {})
            state["tool_results"]["india_vix"] = vix

            rate = await call_tool("market", "get_repo_rate", {})
            state["tool_results"]["repo_rate"] = rate

    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        state["error"] = str(e)

    return state


async def retrieve_context(state: AgentState) -> AgentState:
    """Node 4: Retrieve regulatory/policy context if needed."""
    state["agent_trace"].append("retrieve_context")
    state["rag_context"] = []

    question_type = state["question_type"]

    # Only retrieve for types that need regulation knowledge
    if question_type in (QuestionType.LOAN_DECISION, QuestionType.INSURANCE_GAP):
        try:
            if question_type == QuestionType.LOAN_DECISION:
                result = await call_tool("knowledge", "retrieve_tax_rules", {
                    "query": "home loan interest deduction 80C 24b",
                })
            else:
                result = await call_tool("knowledge", "retrieve_insurance_clause", {
                    "user_id": state["user_id"],
                    "query": state["question"],
                })

            if isinstance(result, dict) and "results" in result:
                for item in result["results"][:3]:
                    if isinstance(item, dict):
                        state["rag_context"].append(json.dumps(item))
                    else:
                        state["rag_context"].append(str(item))
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")

    return state


async def score_risk(state: AgentState) -> AgentState:
    """Node 5: Get financial stress score from RiskMCP."""
    state["agent_trace"].append("score_risk")

    profile = state.get("user_profile", {})
    income = profile.get("monthly_income", 150000)
    expenses = profile.get("monthly_expenses", 80000)

    try:
        result = await call_tool("risk", "predict_financial_stress", {
            "monthly_income": income,
            "monthly_expenses": expenses,
            "debt_to_income": 0.25,
            "emergency_months": 6,
            "equity_pct": 0.4,
            "n_loans": len(profile.get("loans", [])) or 1,
            "insurance_score": 0.7,
            "age": profile.get("age", 30),
            "n_dependents": profile.get("dependents", 1),
        })
        state["risk_score"] = result
    except Exception as e:
        logger.warning(f"Risk scoring failed: {e}")
        state["risk_score"] = {"score": 0, "category": "low", "top_factors": []}

    return state


async def generate_recommendation(state: AgentState) -> AgentState:
    """Node 6: LLM interprets tool outputs and generates recommendation."""
    state["agent_trace"].append("generate_recommendation")

    profile_str = json.dumps(state.get("user_profile", {}), indent=2, default=str)
    tool_str = json.dumps(state.get("tool_results", {}), indent=2, default=str)
    risk_str = json.dumps(state.get("risk_score", {}), indent=2, default=str)
    rag_str = "\n".join(state.get("rag_context", [])) or "No additional context."

    user_msg = RECOMMENDATION_USER_TEMPLATE.format(
        question=state["question"],
        question_type=state["question_type"],
        user_profile=profile_str,
        tool_results=tool_str,
        risk_score=risk_str,
        rag_context=rag_str,
    )

    llm_response = await _call_llm(RECOMMENDATION_SYSTEM_PROMPT, user_msg)

    # Parse LLM JSON response
    try:
        if llm_response:
            # Try to extract JSON from response
            json_start = llm_response.find("{")
            json_end = llm_response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                parsed = json.loads(llm_response[json_start:json_end])
                state["recommendation"] = {
                    "headline": parsed.get("headline", "Analysis Complete"),
                    "reasoning": parsed.get("reasoning", "See quantitative summary for details."),
                    "action_items": parsed.get("action_items", []),
                    "confidence": float(parsed.get("confidence", 0.7)),
                }
                return state
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse LLM response: {e}")

    # Fallback: generate recommendation from tool results
    state["recommendation"] = _generate_fallback_recommendation(state)
    return state


def _generate_fallback_recommendation(state: AgentState) -> dict:
    """Generate a structured recommendation from tool results without LLM."""
    question_type = state.get("question_type", "")
    tools = state.get("tool_results", {})

    if question_type == QuestionType.LOAN_DECISION:
        prepayment = tools.get("prepayment", {})
        mc = tools.get("monte_carlo", {})
        interest_saved = prepayment.get("interest_saved", 0)
        mc_p50 = mc.get("final_value", {}).get("p50", 0) if isinstance(mc.get("final_value"), dict) else 0

        return {
            "headline": f"{'Invest' if mc_p50 > interest_saved else 'Prepay'} — NPV analysis favors this option",
            "reasoning": (
                f"Prepaying ₹{prepayment.get('prepayment_amount', 0):,.0f} on your loan saves "
                f"₹{interest_saved:,.0f} in interest and reduces tenure by "
                f"{prepayment.get('months_reduced', 0)} months. "
                f"Alternatively, investing the same amount with 12% expected annual return "
                f"yields a median value of ₹{mc_p50:,.0f} (P50) over the remaining tenure. "
                f"The P10 (pessimistic) scenario yields ₹{mc.get('final_value', {}).get('p10', 0):,.0f} "
                f"and P90 (optimistic) yields ₹{mc.get('final_value', {}).get('p90', 0):,.0f}. "
                "Educational decision support only. Not financial advice."
            ),
            "action_items": [
                "Compare the guaranteed interest savings from prepayment vs probabilistic investment returns",
                "Consider your risk tolerance — prepayment is guaranteed, investment is probabilistic",
                "Check Section 24(b) tax benefit on home loan interest before prepaying",
                "If investing, use a diversified index fund for the assumed 12% return",
            ],
            "confidence": 0.75,
        }

    elif question_type == QuestionType.SCENARIO_PLANNING:
        stress = tools.get("stress_test", {})
        return {
            "headline": f"{'Feasible' if stress.get('survives', False) else 'Not Feasible'} — {stress.get('months_of_runway', 0):.0f} months of runway",
            "reasoning": (
                f"With monthly expenses of ₹{stress.get('monthly_expenses', 0):,.0f} and "
                f"emergency fund of ₹{stress.get('emergency_fund', 0):,.0f}, you have "
                f"{stress.get('months_of_runway', 0):.1f} months of runway. "
                f"{'You can survive' if stress.get('survives', False) else 'You cannot survive'} "
                f"a {stress.get('income_loss_months', 0)}-month income loss. "
                f"Shortfall: ₹{stress.get('shortfall', 0):,.0f}. "
                "Educational decision support only. Not financial advice."
            ),
            "action_items": [
                f"{'Your emergency fund is sufficient' if stress.get('survives') else 'Build emergency fund to cover the shortfall'}",
                "Consider additional passive income sources",
                "Review and potentially reduce discretionary expenses",
            ],
            "confidence": 0.8,
        }

    elif question_type == QuestionType.INSURANCE_GAP:
        adequacy = tools.get("adequacy", {})
        return {
            "headline": f"{'Adequately Insured' if adequacy.get('is_adequate', False) else 'UNDERINSURED'} — {adequacy.get('adequacy_pct', 0):.0f}% coverage",
            "reasoning": (
                f"Required coverage: ₹{adequacy.get('required_coverage', 0):,.0f}. "
                f"Current coverage: ₹{adequacy.get('current_coverage', 0):,.0f}. "
                f"Coverage gap: ₹{adequacy.get('gap', 0):,.0f}. "
                f"{adequacy.get('recommendation', '')} "
                "Educational decision support only. Not financial advice."
            ),
            "action_items": [
                "Review existing term insurance policies",
                "Consider increasing coverage by ₹{:,.0f}".format(adequacy.get("gap", 0)) if adequacy.get("gap", 0) > 0 else "Coverage is adequate",
                "Compare term plans with claim settlement ratio > 95%",
            ],
            "confidence": 0.85,
        }

    # Default
    return {
        "headline": "Analysis completed — see quantitative details",
        "reasoning": f"Tool results: {json.dumps(tools, indent=2, default=str)[:500]}. "
                     "Educational decision support only. Not financial advice.",
        "action_items": ["Review the quantitative summary for details"],
        "confidence": 0.5,
    }


async def format_output(state: AgentState) -> AgentState:
    """Node 7: Assemble final DecisionOutput."""
    state["agent_trace"].append("format_output")

    processing_time = (time.time() - state.get("start_time", time.time())) * 1000

    rec = state.get("recommendation", {})
    tools = state.get("tool_results", {})
    risk = state.get("risk_score", {})

    # Build quantitative summary
    metrics = {}
    if "emi" in tools:
        metrics["monthly_emi"] = tools["emi"].get("monthly_emi", 0)
    if "prepayment" in tools:
        metrics["interest_saved"] = tools["prepayment"].get("interest_saved", 0)
        metrics["months_reduced"] = tools["prepayment"].get("months_reduced", 0)
    if "monte_carlo" in tools:
        fv = tools["monte_carlo"].get("final_value", {})
        if isinstance(fv, dict):
            metrics["investment_p50"] = fv.get("p50", 0)
    if "stress_test" in tools:
        metrics["months_of_runway"] = tools["stress_test"].get("months_of_runway", 0)
    if "adequacy" in tools:
        metrics["coverage_pct"] = tools["adequacy"].get("adequacy_pct", 0)

    state["quantitative_summary"] = {"metrics": metrics}
    state["processing_time_ms"] = processing_time

    return state


# ============================================================
# Orchestrator Entry Point
# ============================================================

async def run_orchestrator(user_id: int, question: str, db=None) -> DecisionOutput | ScopeError:
    """
    Main entry point: runs the full agent pipeline.

    Args:
        user_id: Authenticated user's ID
        question: Natural language financial question
        db: Optional database session for loading user profile

    Returns:
        DecisionOutput or ScopeError
    """
    state: AgentState = {
        "user_id": user_id,
        "question": question,
        "agent_trace": [],
    }

    # Run pipeline sequentially
    state = await classify_question(state)

    # Check out-of-scope
    if state["question_type"] == QuestionType.OUT_OF_SCOPE:
        return ScopeError(
            question=question,
            reason="This question is outside the scope of the Financial Intelligence Engine.",
        )

    state = await load_user_profile(state)
    state = await execute_tools(state)
    state = await retrieve_context(state)
    state = await score_risk(state)
    state = await generate_recommendation(state)
    state = await format_output(state)

    # Assemble output
    rec = state.get("recommendation", {})
    risk = state.get("risk_score", {})

    risk_result = None
    if risk:
        top_factors = []
        for f in risk.get("top_factors", []):
            if isinstance(f, dict):
                top_factors.append(RiskFactor(**f))
            elif isinstance(f, RiskFactor):
                top_factors.append(f)

        risk_result = FinancialStressResult(
            score=risk.get("score", 0),
            category=RiskCategory(risk.get("category", "low")),
            top_factors=top_factors,
        )

    return DecisionOutput(
        user_id=user_id,
        question=question,
        question_type=QuestionType(state["question_type"]) if isinstance(state["question_type"], str) else state["question_type"],
        recommendation=DecisionRecommendation(
            headline=rec.get("headline", "Analysis Complete"),
            reasoning=rec.get("reasoning", "See quantitative summary."),
            action_items=rec.get("action_items", []),
            confidence=rec.get("confidence", 0.5),
        ),
        quantitative_summary=QuantitativeSummary(
            metrics=state.get("quantitative_summary", {}).get("metrics", {}),
        ),
        risk_score=risk_result,
        rag_context=state.get("rag_context", []),
        agent_trace=state.get("agent_trace", []),
        processing_time_ms=state.get("processing_time_ms", 0),
        timestamp=datetime.utcnow(),
    )
