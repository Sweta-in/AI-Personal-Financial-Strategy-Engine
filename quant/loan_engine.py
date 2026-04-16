"""
Loan Engine — Pure Python loan computation module.

All functions return typed Pydantic models.
The LLM never calculates math — it only interprets these outputs.
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.app.schemas.models import (
    AmortizationRow,
    AmortizationSchedule,
    DebtToIncomeResult,
    EMIResult,
    PrepaymentBenefit,
    RefinanceResult,
)


def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> EMIResult:
    """
    Calculate EMI using the standard reducing-balance formula.

    EMI = P * r * (1+r)^n / ((1+r)^n - 1)

    where:
        P = principal amount
        r = monthly interest rate (annual_rate / 12 / 100)
        n = tenure in months

    Args:
        principal: Loan principal amount
        annual_rate: Annual interest rate in percentage (e.g., 8.5 for 8.5%)
        tenure_months: Loan tenure in months

    Returns:
        EMIResult with monthly_emi, total_payment, total_interest
    """
    if principal <= 0:
        raise ValueError("Principal must be positive")
    if annual_rate <= 0:
        raise ValueError("Annual rate must be positive")
    if tenure_months <= 0:
        raise ValueError("Tenure must be positive")

    monthly_rate = annual_rate / 12 / 100
    factor = (1 + monthly_rate) ** tenure_months

    monthly_emi = principal * monthly_rate * factor / (factor - 1)
    total_payment = monthly_emi * tenure_months
    total_interest = total_payment - principal

    return EMIResult(
        principal=round(principal, 2),
        annual_rate=annual_rate,
        tenure_months=tenure_months,
        monthly_emi=round(monthly_emi, 2),
        total_payment=round(total_payment, 2),
        total_interest=round(total_interest, 2),
    )


def build_amortization_schedule(
    principal: float,
    annual_rate: float,
    tenure_months: int,
) -> AmortizationSchedule:
    """
    Build a month-by-month amortization schedule showing principal and interest
    components of each EMI payment.

    Args:
        principal: Loan principal amount
        annual_rate: Annual interest rate in percentage
        tenure_months: Loan tenure in months

    Returns:
        AmortizationSchedule with full schedule and totals
    """
    emi_result = calculate_emi(principal, annual_rate, tenure_months)
    monthly_rate = annual_rate / 12 / 100
    emi = emi_result.monthly_emi

    schedule: list[AmortizationRow] = []
    balance = principal
    total_interest = 0.0

    for month in range(1, tenure_months + 1):
        interest_component = round(balance * monthly_rate, 2)
        principal_component = round(emi - interest_component, 2)

        # Handle last month rounding
        if month == tenure_months:
            principal_component = round(balance, 2)
            interest_component = round(emi - principal_component, 2) if emi > principal_component else 0.0

        closing_balance = round(balance - principal_component, 2)
        if closing_balance < 0:
            closing_balance = 0.0

        total_interest += interest_component

        schedule.append(
            AmortizationRow(
                month=month,
                opening_balance=round(balance, 2),
                emi=round(emi, 2),
                principal_component=principal_component,
                interest_component=interest_component,
                closing_balance=closing_balance,
            )
        )

        balance = closing_balance

    return AmortizationSchedule(
        principal=round(principal, 2),
        annual_rate=annual_rate,
        tenure_months=tenure_months,
        monthly_emi=round(emi, 2),
        schedule=schedule,
        total_interest=round(total_interest, 2),
        total_payment=round(principal + total_interest, 2),
    )


def calculate_prepayment_benefit(
    outstanding: float,
    annual_rate: float,
    remaining_months: int,
    prepayment_amount: float,
) -> PrepaymentBenefit:
    """
    Calculate the benefit of making a lump-sum prepayment on a loan.
    Assumes prepayment reduces the principal and tenure is recalculated
    keeping EMI constant.

    Args:
        outstanding: Current outstanding loan balance
        annual_rate: Annual interest rate in percentage
        remaining_months: Remaining tenure in months
        prepayment_amount: Lump-sum prepayment amount

    Returns:
        PrepaymentBenefit with interest saved and months reduced
    """
    if prepayment_amount >= outstanding:
        raise ValueError("Prepayment amount must be less than outstanding balance")
    if prepayment_amount <= 0:
        raise ValueError("Prepayment amount must be positive")

    # Original scenario
    original_emi = calculate_emi(outstanding, annual_rate, remaining_months)
    original_total_interest = original_emi.total_interest

    # After prepayment: new principal, same EMI → solve for new tenure
    new_principal = outstanding - prepayment_amount
    monthly_rate = annual_rate / 12 / 100
    emi = original_emi.monthly_emi

    # n = -log(1 - P*r/EMI) / log(1+r)
    import math

    ratio = 1 - (new_principal * monthly_rate / emi)
    if ratio <= 0:
        # EMI is too small for the new principal (should not happen with valid inputs)
        raise ValueError("EMI insufficient for new principal — check inputs")

    new_tenure_months = math.ceil(-math.log(ratio) / math.log(1 + monthly_rate))
    months_reduced = remaining_months - new_tenure_months

    # Calculate new total interest
    new_total_interest = (emi * new_tenure_months) - new_principal
    interest_saved = original_total_interest - new_total_interest

    return PrepaymentBenefit(
        prepayment_amount=round(prepayment_amount, 2),
        interest_saved=round(interest_saved, 2),
        months_reduced=months_reduced,
        new_tenure_months=new_tenure_months,
        original_total_interest=round(original_total_interest, 2),
        new_total_interest=round(new_total_interest, 2),
    )


def refinance_break_even(
    old_rate: float,
    new_rate: float,
    outstanding: float,
    remaining_months: int,
    processing_fee: float,
) -> RefinanceResult:
    """
    Calculate when refinancing breaks even after paying the processing fee.

    Args:
        old_rate: Current annual interest rate (%)
        new_rate: New annual interest rate (%)
        outstanding: Outstanding loan balance
        remaining_months: Remaining tenure in months
        processing_fee: One-time processing fee for refinancing

    Returns:
        RefinanceResult with break-even months and total savings
    """
    if new_rate >= old_rate:
        return RefinanceResult(
            old_rate=old_rate,
            new_rate=new_rate,
            processing_fee=processing_fee,
            monthly_savings=0.0,
            break_even_months=0,
            total_savings_over_tenure=0.0,
            recommendation="Refinancing not beneficial — new rate is not lower than current rate.",
        )

    old_emi = calculate_emi(outstanding, old_rate, remaining_months).monthly_emi
    new_emi = calculate_emi(outstanding, new_rate, remaining_months).monthly_emi
    monthly_savings = old_emi - new_emi

    import math

    if monthly_savings > 0:
        break_even_months = math.ceil(processing_fee / monthly_savings)
    else:
        break_even_months = 0

    total_savings = (monthly_savings * remaining_months) - processing_fee

    if total_savings > 0:
        recommendation = (
            f"Refinance recommended. You recover the ₹{processing_fee:,.0f} processing fee "
            f"in {break_even_months} months and save ₹{total_savings:,.0f} over the remaining tenure."
        )
    else:
        recommendation = (
            f"Refinancing not recommended. Total savings of ₹{monthly_savings * remaining_months:,.0f} "
            f"do not cover the ₹{processing_fee:,.0f} processing fee."
        )

    return RefinanceResult(
        old_rate=old_rate,
        new_rate=new_rate,
        processing_fee=round(processing_fee, 2),
        monthly_savings=round(monthly_savings, 2),
        break_even_months=break_even_months,
        total_savings_over_tenure=round(total_savings, 2),
        recommendation=recommendation,
    )


def debt_to_income_ratio(
    total_monthly_debt: float,
    monthly_income: float,
) -> DebtToIncomeResult:
    """
    Calculate debt-to-income ratio and categorize financial health.

    Args:
        total_monthly_debt: Sum of all monthly debt payments (EMIs, credit cards, etc.)
        monthly_income: Gross monthly income

    Returns:
        DebtToIncomeResult with ratio, category, and recommendation
    """
    if monthly_income <= 0:
        raise ValueError("Monthly income must be positive")

    dti = total_monthly_debt / monthly_income

    if dti <= 0.20:
        category = "Healthy"
        recommendation = "Your debt-to-income ratio is well within healthy limits. You have strong capacity for additional borrowing if needed."
    elif dti <= 0.36:
        category = "Manageable"
        recommendation = "Your debt-to-income ratio is manageable but approaching caution territory. Avoid taking on significant new debt."
    elif dti <= 0.50:
        category = "Stressed"
        recommendation = "Your debt-to-income ratio is high. Consider debt consolidation or accelerated repayment strategies."
    else:
        category = "Critical"
        recommendation = "Your debt-to-income ratio is critically high. Immediate debt reduction is strongly recommended."

    return DebtToIncomeResult(
        total_monthly_debt=round(total_monthly_debt, 2),
        monthly_income=round(monthly_income, 2),
        dti_ratio=round(dti, 4),
        category=category,
        recommendation=recommendation,
    )
