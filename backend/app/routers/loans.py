"""
Loans router — CRUD for loan entities + quant calculations.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.dependencies import get_current_user
from backend.app.models.db_models import Loan, User
from backend.app.schemas.models import (
    AmortizationSchedule,
    EMIResult,
    LoanCreate,
    LoanResponse,
    LoanUpdate,
    PrepaymentBenefit,
)
from quant.loan_engine import (
    build_amortization_schedule,
    calculate_emi,
    calculate_prepayment_benefit,
)

router = APIRouter(prefix="/api/loans", tags=["Loans"])


@router.post("/", response_model=LoanResponse, status_code=201)
async def create_loan(
    loan_data: LoanCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new loan record."""
    # Auto-calculate EMI if not provided
    emi = loan_data.emi
    if emi is None:
        emi_result = calculate_emi(loan_data.principal, loan_data.annual_rate, loan_data.tenure_months)
        emi = emi_result.monthly_emi

    loan = Loan(
        user_id=current_user.id,
        name=loan_data.name,
        loan_type=loan_data.loan_type,
        principal=loan_data.principal,
        annual_rate=loan_data.annual_rate,
        tenure_months=loan_data.tenure_months,
        outstanding_balance=loan_data.outstanding_balance,
        emi=emi,
        start_date=loan_data.start_date,
    )
    db.add(loan)
    await db.flush()
    await db.refresh(loan)
    return LoanResponse.model_validate(loan)


@router.get("/", response_model=list[LoanResponse])
async def list_loans(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all loans for the current user."""
    result = await db.execute(select(Loan).where(Loan.user_id == current_user.id))
    return [LoanResponse.model_validate(loan) for loan in result.scalars().all()]


@router.get("/{loan_id}", response_model=LoanResponse)
async def get_loan(
    loan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific loan by ID."""
    result = await db.execute(
        select(Loan).where(Loan.id == loan_id, Loan.user_id == current_user.id)
    )
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    return LoanResponse.model_validate(loan)


@router.put("/{loan_id}", response_model=LoanResponse)
async def update_loan(
    loan_id: int,
    loan_data: LoanUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing loan."""
    result = await db.execute(
        select(Loan).where(Loan.id == loan_id, Loan.user_id == current_user.id)
    )
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")

    update_data = loan_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(loan, field, value)

    await db.flush()
    await db.refresh(loan)
    return LoanResponse.model_validate(loan)


@router.delete("/{loan_id}", status_code=204)
async def delete_loan(
    loan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a loan."""
    result = await db.execute(
        select(Loan).where(Loan.id == loan_id, Loan.user_id == current_user.id)
    )
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    await db.delete(loan)


@router.get("/{loan_id}/amortization", response_model=AmortizationSchedule)
async def get_amortization(
    loan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate amortization schedule for a loan."""
    result = await db.execute(
        select(Loan).where(Loan.id == loan_id, Loan.user_id == current_user.id)
    )
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    return build_amortization_schedule(loan.principal, loan.annual_rate, loan.tenure_months)


@router.post("/{loan_id}/prepayment", response_model=PrepaymentBenefit)
async def simulate_prepayment(
    loan_id: int,
    prepayment_amount: float,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Simulate prepayment benefit for a loan."""
    result = await db.execute(
        select(Loan).where(Loan.id == loan_id, Loan.user_id == current_user.id)
    )
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")

    return calculate_prepayment_benefit(
        outstanding=loan.outstanding_balance,
        annual_rate=loan.annual_rate,
        remaining_months=loan.tenure_months,
        prepayment_amount=prepayment_amount,
    )


@router.post("/calculate-emi", response_model=EMIResult)
async def calculate_emi_endpoint(
    principal: float,
    annual_rate: float,
    tenure_months: int,
):
    """Calculate EMI without creating a loan record (public endpoint)."""
    return calculate_emi(principal, annual_rate, tenure_months)
