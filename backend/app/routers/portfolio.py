"""
Portfolio router — CRUD for holdings + Monte Carlo simulation.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.dependencies import get_current_user
from backend.app.models.db_models import PortfolioHolding, User
from backend.app.schemas.models import (
    MonteCarloResult,
    PortfolioHoldingCreate,
    PortfolioHoldingResponse,
)
from quant.simulation_engine import monte_carlo_portfolio_growth

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])


@router.post("/holdings", response_model=PortfolioHoldingResponse, status_code=201)
async def create_holding(
    data: PortfolioHoldingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a new portfolio holding."""
    holding = PortfolioHolding(
        user_id=current_user.id,
        symbol=data.symbol,
        name=data.name,
        asset_type=data.asset_type,
        quantity=data.quantity,
        avg_buy_price=data.avg_buy_price,
        current_price=data.current_price,
    )
    db.add(holding)
    await db.flush()
    await db.refresh(holding)
    return PortfolioHoldingResponse.model_validate(holding)


@router.get("/holdings", response_model=list[PortfolioHoldingResponse])
async def list_holdings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all portfolio holdings."""
    result = await db.execute(
        select(PortfolioHolding).where(PortfolioHolding.user_id == current_user.id)
    )
    return [PortfolioHoldingResponse.model_validate(h) for h in result.scalars().all()]


@router.delete("/holdings/{holding_id}", status_code=204)
async def delete_holding(
    holding_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a portfolio holding."""
    result = await db.execute(
        select(PortfolioHolding).where(
            PortfolioHolding.id == holding_id,
            PortfolioHolding.user_id == current_user.id,
        )
    )
    holding = result.scalar_one_or_none()
    if not holding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found")
    await db.delete(holding)


@router.post("/simulate", response_model=MonteCarloResult)
async def simulate_portfolio(
    initial_value: float,
    monthly_sip: float,
    annual_return_mean: float = 0.12,
    annual_return_std: float = 0.18,
    time_horizon_months: int = 120,
    n_simulations: int = 10000,
):
    """Run Monte Carlo portfolio simulation — no login required."""
    return monte_carlo_portfolio_growth(
        initial_value=initial_value,
        monthly_sip=monthly_sip,
        annual_return_mean=annual_return_mean,
        annual_return_std=annual_return_std,
        time_horizon_months=time_horizon_months,
        n_simulations=n_simulations,
    )
