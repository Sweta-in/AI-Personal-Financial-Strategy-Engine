"""
Financial router — net worth, financial goals, income sources.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.dependencies import get_current_user
from backend.app.models.db_models import (
    Asset,
    FinancialGoal,
    IncomeSource,
    Loan,
    User,
)
from backend.app.schemas.models import (
    FinancialGoalCreate,
    FinancialGoalResponse,
    FinancialGoalUpdate,
    IncomeSourceCreate,
    IncomeSourceResponse,
    NetWorthResult,
)
from quant.portfolio_engine import net_worth

router = APIRouter(prefix="/api/financial", tags=["Financial"])


# --- Net Worth ---

@router.get("/net-worth", response_model=NetWorthResult)
async def get_net_worth(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Calculate user's net worth from assets and liabilities."""
    # Fetch assets
    asset_result = await db.execute(select(Asset).where(Asset.user_id == current_user.id))
    assets_db = asset_result.scalars().all()
    assets = {a.name: a.current_value for a in assets_db}

    # Fetch liabilities (loans)
    loan_result = await db.execute(select(Loan).where(Loan.user_id == current_user.id))
    loans_db = loan_result.scalars().all()
    liabilities = {l.name: l.outstanding_balance for l in loans_db}

    return net_worth(assets, liabilities)


# --- Income Sources ---

@router.post("/income-sources", response_model=IncomeSourceResponse, status_code=201)
async def create_income_source(
    data: IncomeSourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new income source."""
    source = IncomeSource(
        user_id=current_user.id,
        name=data.name,
        amount=data.amount,
        frequency=data.frequency,
        is_active=data.is_active,
    )
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return IncomeSourceResponse.model_validate(source)


@router.get("/income-sources", response_model=list[IncomeSourceResponse])
async def list_income_sources(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all income sources."""
    result = await db.execute(select(IncomeSource).where(IncomeSource.user_id == current_user.id))
    return [IncomeSourceResponse.model_validate(s) for s in result.scalars().all()]


# --- Financial Goals ---

@router.post("/goals", response_model=FinancialGoalResponse, status_code=201)
async def create_goal(
    data: FinancialGoalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new financial goal."""
    goal = FinancialGoal(
        user_id=current_user.id,
        name=data.name,
        target_amount=data.target_amount,
        current_amount=data.current_amount,
        target_date=data.target_date,
        monthly_contribution=data.monthly_contribution,
        status=data.status,
    )
    db.add(goal)
    await db.flush()
    await db.refresh(goal)
    return FinancialGoalResponse.model_validate(goal)


@router.get("/goals", response_model=list[FinancialGoalResponse])
async def list_goals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all financial goals."""
    result = await db.execute(select(FinancialGoal).where(FinancialGoal.user_id == current_user.id))
    return [FinancialGoalResponse.model_validate(g) for g in result.scalars().all()]


@router.put("/goals/{goal_id}", response_model=FinancialGoalResponse)
async def update_goal(
    goal_id: int,
    data: FinancialGoalUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a financial goal."""
    result = await db.execute(
        select(FinancialGoal).where(FinancialGoal.id == goal_id, FinancialGoal.user_id == current_user.id)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)

    await db.flush()
    await db.refresh(goal)
    return FinancialGoalResponse.model_validate(goal)


@router.delete("/goals/{goal_id}", status_code=204)
async def delete_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a financial goal."""
    result = await db.execute(
        select(FinancialGoal).where(FinancialGoal.id == goal_id, FinancialGoal.user_id == current_user.id)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    await db.delete(goal)
