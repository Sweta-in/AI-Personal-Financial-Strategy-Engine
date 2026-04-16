"""
Decisions router — triggers the LangGraph orchestrator for financial decisions.
"""

from __future__ import annotations

import json
import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.dependencies import get_current_user
from backend.app.models.db_models import DecisionLog, User
from backend.app.schemas.models import (
    DecisionLogResponse,
    DecisionOutput,
    DecisionRequest,
    ScopeError,
)

router = APIRouter(prefix="/api/decisions", tags=["Decisions"])


# Out-of-scope patterns — hard-coded rejection
_OUT_OF_SCOPE_PATTERNS = [
    "which stock will",
    "which share will",
    "should i buy",
    "should i sell",
    "will market crash",
    "will stock go up",
    "predict market",
    "stock recommendation",
    "best stock",
    "crypto",
    "bitcoin",
]


def _is_out_of_scope(question: str) -> bool:
    """Check if a question is out of scope for the engine."""
    q_lower = question.lower()
    return any(pattern in q_lower for pattern in _OUT_OF_SCOPE_PATTERNS)


@router.post("/ask", response_model=DecisionOutput | ScopeError)
async def ask_decision(
    request: DecisionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Ask a financial decision question.
    Triggers the LangGraph orchestrator pipeline.
    """
    # Hard-coded rejection for out-of-scope questions
    if _is_out_of_scope(request.question):
        return ScopeError(
            question=request.question,
            reason="This question is outside the scope of the Financial Intelligence Engine. "
                   "We provide decision support for structured financial planning, not "
                   "stock picks or market predictions.",
        )

    start = time.time()

    try:
        # Import orchestrator lazily to avoid circular imports
        from agents.orchestrator import run_orchestrator

        result = await run_orchestrator(
            user_id=current_user.id,
            question=request.question,
            db=db,
        )
    except ImportError:
        # Orchestrator not yet built (Phase 4) — return placeholder
        from datetime import datetime
        from backend.app.schemas.models import (
            DecisionRecommendation,
            QuestionType,
            QuantitativeSummary,
        )

        processing_time = (time.time() - start) * 1000
        result = DecisionOutput(
            user_id=current_user.id,
            question=request.question,
            question_type=QuestionType.LOAN_DECISION,
            recommendation=DecisionRecommendation(
                headline="Orchestrator not yet initialized",
                reasoning="The LangGraph orchestrator (Phase 4) has not been built yet. "
                          "This is a placeholder response.",
                action_items=["Complete Phase 4 — LangGraph Orchestration"],
                confidence=0.0,
            ),
            quantitative_summary=QuantitativeSummary(metrics={}),
            agent_trace=["placeholder_response"],
            processing_time_ms=processing_time,
            timestamp=datetime.utcnow(),
        )

    processing_time = (time.time() - start) * 1000

    # Log the decision
    log = DecisionLog(
        user_id=current_user.id,
        question=request.question,
        question_type=result.question_type if isinstance(result, DecisionOutput) else "out_of_scope",
        recommendation_headline=result.recommendation.headline if isinstance(result, DecisionOutput) else "Out of scope",
        recommendation_reasoning=result.recommendation.reasoning if isinstance(result, DecisionOutput) else result.reason,
        quantitative_summary_json=json.dumps(result.quantitative_summary.metrics, default=str) if isinstance(result, DecisionOutput) else "{}",
        risk_score=result.risk_score.score if isinstance(result, DecisionOutput) and result.risk_score else None,
        processing_time_ms=processing_time,
    )
    db.add(log)

    return result


@router.get("/history", response_model=list[DecisionLogResponse])
async def decision_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get decision history for the current user."""
    from sqlalchemy import select

    result = await db.execute(
        select(DecisionLog)
        .where(DecisionLog.user_id == current_user.id)
        .order_by(DecisionLog.created_at.desc())
        .limit(limit)
    )
    return [DecisionLogResponse.model_validate(d) for d in result.scalars().all()]
