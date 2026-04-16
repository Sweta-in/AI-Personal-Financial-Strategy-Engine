"""
Orchestrator tests — end-to-end agent pipeline tests.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agents.orchestrator import classify_question, run_orchestrator, AgentState
from backend.app.schemas.models import DecisionOutput, QuestionType, ScopeError


@pytest.mark.asyncio
async def test_classify_loan_question():
    state: AgentState = {
        "user_id": 1,
        "question": "Should I prepay my home loan or invest in mutual funds?",
        "agent_trace": [],
    }
    result = await classify_question(state)
    assert result["question_type"] == QuestionType.LOAN_DECISION


@pytest.mark.asyncio
async def test_classify_insurance_question():
    state: AgentState = {
        "user_id": 1,
        "question": "Am I underinsured for my 2 dependents?",
        "agent_trace": [],
    }
    result = await classify_question(state)
    assert result["question_type"] == QuestionType.INSURANCE_GAP


@pytest.mark.asyncio
async def test_classify_scenario_question():
    state: AgentState = {
        "user_id": 1,
        "question": "Can I afford a 6-month career break given my savings?",
        "agent_trace": [],
    }
    result = await classify_question(state)
    assert result["question_type"] == QuestionType.SCENARIO_PLANNING


@pytest.mark.asyncio
async def test_classify_out_of_scope():
    state: AgentState = {
        "user_id": 1,
        "question": "Which stock will go up tomorrow?",
        "agent_trace": [],
    }
    result = await classify_question(state)
    assert result["question_type"] == QuestionType.OUT_OF_SCOPE


@pytest.mark.asyncio
async def test_reject_out_of_scope():
    result = await run_orchestrator(
        user_id=1,
        question="Should I buy Reliance stock?",
    )
    assert isinstance(result, ScopeError)
    assert result.question_type == QuestionType.OUT_OF_SCOPE


@pytest.mark.asyncio
async def test_full_loan_pipeline():
    result = await run_orchestrator(
        user_id=1,
        question="Should I prepay my ₹30L home loan at 8.5% or invest the surplus in index funds?",
    )
    assert isinstance(result, DecisionOutput)
    assert result.question_type == QuestionType.LOAN_DECISION
    assert result.recommendation.headline
    assert result.recommendation.reasoning
    assert len(result.agent_trace) >= 5
    assert "Educational decision support only" in result.recommendation.disclaimer
    assert result.processing_time_ms > 0


@pytest.mark.asyncio
async def test_full_scenario_pipeline():
    result = await run_orchestrator(
        user_id=1,
        question="Can I afford a 6-month career break?",
    )
    assert isinstance(result, DecisionOutput)
    assert result.question_type == QuestionType.SCENARIO_PLANNING
    assert "months_of_runway" in result.quantitative_summary.metrics


@pytest.mark.asyncio
async def test_full_insurance_pipeline():
    result = await run_orchestrator(
        user_id=1,
        question="Am I underinsured for my 2 dependents?",
    )
    assert isinstance(result, DecisionOutput)
    assert result.question_type == QuestionType.INSURANCE_GAP
    assert result.recommendation.reasoning


@pytest.mark.asyncio
async def test_agent_trace_logged():
    result = await run_orchestrator(
        user_id=1,
        question="Should I increase my SIP amount?",
    )
    if isinstance(result, DecisionOutput):
        assert "classify_question" in result.agent_trace
        assert "execute_tools" in result.agent_trace
        assert "format_output" in result.agent_trace
