"""
Insurance Engine — Insurance coverage analysis using Human Life Value (HLV) method.

All functions return typed Pydantic models.
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.app.schemas.models import (
    HealthInsuranceSufficiencyResult,
    InsuranceAdequacyResult,
    InsuranceCoverageResult,
)


def required_term_coverage(
    annual_income: float,
    age: int,
    dependents: int,
    outstanding_loans: float,
) -> InsuranceCoverageResult:
    """
    Calculate required term insurance coverage using the Human Life Value (HLV) method.

    HLV = Income Replacement + Loan Coverage

    Income Replacement = annual_income * income_multiplier
    where income_multiplier scales with age and dependents:
        - Base: (retirement_age - current_age) years of income
        - Discounted at 6% for present value
        - Adjusted for dependents (1.2x per dependent)

    Loan Coverage = outstanding_loans (full coverage assumed)

    Args:
        annual_income: Current annual income
        age: Current age
        dependents: Number of financial dependents
        outstanding_loans: Total outstanding loan amount

    Returns:
        InsuranceCoverageResult with required coverage breakdown
    """
    if annual_income <= 0:
        raise ValueError("Annual income must be positive")
    if age < 18 or age > 70:
        raise ValueError("Age must be between 18 and 70")
    if dependents < 0:
        raise ValueError("Dependents cannot be negative")
    if outstanding_loans < 0:
        raise ValueError("Outstanding loans cannot be negative")

    retirement_age = 60
    working_years_left = max(0, retirement_age - age)

    # Present value of future income stream, discounted at 6%
    discount_rate = 0.06
    if working_years_left > 0:
        # PV of annuity: income * [(1 - (1+r)^-n) / r]
        pv_factor = (1 - (1 + discount_rate) ** (-working_years_left)) / discount_rate
        income_replacement = annual_income * pv_factor
    else:
        income_replacement = 0.0

    # Dependent multiplier: 20% additional per dependent
    dependent_multiplier = 1.0 + (0.2 * dependents)
    income_replacement *= dependent_multiplier

    # Loan coverage component
    loan_coverage = outstanding_loans

    # Total required coverage
    required_coverage = income_replacement + loan_coverage

    return InsuranceCoverageResult(
        annual_income=round(annual_income, 2),
        age=age,
        dependents=dependents,
        outstanding_loans=round(outstanding_loans, 2),
        required_coverage=round(required_coverage, 2),
        method="HLV",
        income_replacement_component=round(income_replacement, 2),
        loan_coverage_component=round(loan_coverage, 2),
    )


def insurance_adequacy_score(
    current_coverage: float,
    required_coverage: float,
) -> InsuranceAdequacyResult:
    """
    Calculate insurance adequacy as a percentage and identify the gap.

    Args:
        current_coverage: Current total insurance coverage amount
        required_coverage: Required coverage (from required_term_coverage)

    Returns:
        InsuranceAdequacyResult with adequacy percentage and recommendation
    """
    if required_coverage <= 0:
        return InsuranceAdequacyResult(
            current_coverage=current_coverage,
            required_coverage=0,
            adequacy_pct=100.0,
            gap=0.0,
            is_adequate=True,
            recommendation="No coverage requirement identified.",
        )

    adequacy_pct = (current_coverage / required_coverage) * 100
    gap = max(0.0, required_coverage - current_coverage)
    is_adequate = adequacy_pct >= 80  # 80% threshold

    if adequacy_pct >= 100:
        recommendation = (
            f"Your coverage of ₹{current_coverage:,.0f} meets or exceeds the required "
            f"₹{required_coverage:,.0f}. Your dependents are well protected."
        )
    elif adequacy_pct >= 80:
        recommendation = (
            f"Your coverage is at {adequacy_pct:.0f}% of the recommended level. "
            f"Consider increasing coverage by ₹{gap:,.0f} for complete protection."
        )
    elif adequacy_pct >= 50:
        recommendation = (
            f"UNDERINSURED: Your coverage is only {adequacy_pct:.0f}% of what's needed. "
            f"You have a gap of ₹{gap:,.0f}. Strongly recommend increasing term insurance."
        )
    else:
        recommendation = (
            f"CRITICALLY UNDERINSURED: Coverage is only {adequacy_pct:.0f}% of requirement. "
            f"Gap of ₹{gap:,.0f}. Immediate action needed — purchase additional term insurance."
        )

    return InsuranceAdequacyResult(
        current_coverage=round(current_coverage, 2),
        required_coverage=round(required_coverage, 2),
        adequacy_pct=round(adequacy_pct, 2),
        gap=round(gap, 2),
        is_adequate=is_adequate,
        recommendation=recommendation,
    )


def health_insurance_sufficiency(
    current_health_cover: float,
    age: int,
    dependents: int,
    city_tier: int = 1,
) -> HealthInsuranceSufficiencyResult:
    """
    Assess whether health insurance coverage is sufficient based on
    age, dependents, and city tier.

    Rule of thumb for India:
    - Tier 1 city: ₹10L base + ₹5L per dependent
    - Tier 2 city: ₹7L base + ₹3L per dependent
    - Tier 3 city: ₹5L base + ₹2L per dependent
    - Add ₹2L for every decade above 30

    Args:
        current_health_cover: Current health insurance sum insured
        age: Primary insured's age
        dependents: Number of dependents on the policy
        city_tier: City tier (1, 2, or 3)

    Returns:
        HealthInsuranceSufficiencyResult with recommendation
    """
    if city_tier not in (1, 2, 3):
        city_tier = 1

    base_cover = {1: 1000000, 2: 700000, 3: 500000}
    per_dependent = {1: 500000, 2: 300000, 3: 200000}

    recommended = base_cover[city_tier] + (per_dependent[city_tier] * dependents)

    # Age adjustment: ₹2L per decade above 30
    age_decades = max(0, (age - 30) // 10)
    recommended += age_decades * 200000

    gap = max(0.0, recommended - current_health_cover)
    is_sufficient = current_health_cover >= recommended

    if is_sufficient:
        recommendation = (
            f"Your health cover of ₹{current_health_cover:,.0f} meets the recommended "
            f"₹{recommended:,.0f} for a Tier-{city_tier} city."
        )
    else:
        recommendation = (
            f"Your health cover of ₹{current_health_cover:,.0f} falls short of the recommended "
            f"₹{recommended:,.0f}. Consider a top-up plan of ₹{gap:,.0f}."
        )

    return HealthInsuranceSufficiencyResult(
        current_health_cover=round(current_health_cover, 2),
        recommended_cover=round(recommended, 2),
        is_sufficient=is_sufficient,
        gap=round(gap, 2),
        recommendation=recommendation,
    )
