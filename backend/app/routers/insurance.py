"""
Insurance router — CRUD for insurance policies.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.dependencies import get_current_user
from backend.app.models.db_models import Insurance, User
from backend.app.schemas.models import (
    InsuranceAdequacyResult,
    InsuranceCoverageResult,
    InsuranceCreate,
    InsuranceResponse,
    InsuranceUpdate,
)
from quant.insurance_engine import insurance_adequacy_score, required_term_coverage

router = APIRouter(prefix="/api/insurance", tags=["Insurance"])


@router.post("/", response_model=InsuranceResponse, status_code=201)
async def create_policy(
    data: InsuranceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new insurance policy."""
    policy = Insurance(
        user_id=current_user.id,
        name=data.name,
        insurance_type=data.insurance_type,
        provider=data.provider,
        sum_assured=data.sum_assured,
        annual_premium=data.annual_premium,
        policy_start=data.policy_start,
        policy_end=data.policy_end,
        document_url=data.document_url,
    )
    db.add(policy)
    await db.flush()
    await db.refresh(policy)
    return InsuranceResponse.model_validate(policy)


@router.get("/", response_model=list[InsuranceResponse])
async def list_policies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all insurance policies for the current user."""
    result = await db.execute(select(Insurance).where(Insurance.user_id == current_user.id))
    return [InsuranceResponse.model_validate(p) for p in result.scalars().all()]


@router.get("/{policy_id}", response_model=InsuranceResponse)
async def get_policy(
    policy_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific policy."""
    result = await db.execute(
        select(Insurance).where(Insurance.id == policy_id, Insurance.user_id == current_user.id)
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return InsuranceResponse.model_validate(policy)


@router.put("/{policy_id}", response_model=InsuranceResponse)
async def update_policy(
    policy_id: int,
    data: InsuranceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing insurance policy."""
    result = await db.execute(
        select(Insurance).where(Insurance.id == policy_id, Insurance.user_id == current_user.id)
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(policy, field, value)

    await db.flush()
    await db.refresh(policy)
    return InsuranceResponse.model_validate(policy)


@router.delete("/{policy_id}", status_code=204)
async def delete_policy(
    policy_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an insurance policy."""
    result = await db.execute(
        select(Insurance).where(Insurance.id == policy_id, Insurance.user_id == current_user.id)
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    await db.delete(policy)


@router.post("/gap-analysis", response_model=InsuranceAdequacyResult)
async def gap_analysis(
    annual_income: float,
    age: int,
    dependents: int,
    outstanding_loans: float,
    current_coverage: float,
):
    """Run insurance gap analysis — no login required."""
    coverage = required_term_coverage(annual_income, age, dependents, outstanding_loans)
    return insurance_adequacy_score(current_coverage, coverage.required_coverage)
