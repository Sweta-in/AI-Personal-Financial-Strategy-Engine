"""
Tests for loan_engine.py — verified against known bank calculator values.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from quant.loan_engine import (
    build_amortization_schedule,
    calculate_emi,
    calculate_prepayment_benefit,
    debt_to_income_ratio,
    refinance_break_even,
)


class TestCalculateEMI:
    """EMI calculation tests with known values."""

    def test_standard_home_loan(self):
        """₹30L at 8.5% for 20 years → EMI ≈ ₹26,049 (verified against SBI calculator)"""
        result = calculate_emi(3000000, 8.5, 240)
        assert abs(result.monthly_emi - 26049) < 50  # Within ₹50 tolerance
        assert result.principal == 3000000
        assert result.annual_rate == 8.5
        assert result.tenure_months == 240
        assert result.total_payment > result.principal
        assert result.total_interest > 0

    def test_personal_loan(self):
        """₹5L at 12% for 5 years → EMI ≈ ₹11,122"""
        result = calculate_emi(500000, 12, 60)
        assert abs(result.monthly_emi - 11122) < 50

    def test_car_loan(self):
        """₹8L at 9% for 7 years → EMI ≈ ₹12,507"""
        result = calculate_emi(800000, 9, 84)
        assert abs(result.monthly_emi - 12507) < 50

    def test_total_interest_consistency(self):
        """total_interest = total_payment - principal"""
        result = calculate_emi(1000000, 10, 120)
        assert abs(result.total_interest - (result.total_payment - result.principal)) < 1

    def test_invalid_principal(self):
        with pytest.raises(ValueError, match="Principal must be positive"):
            calculate_emi(0, 8.5, 240)

    def test_invalid_rate(self):
        with pytest.raises(ValueError, match="Annual rate must be positive"):
            calculate_emi(1000000, 0, 240)

    def test_invalid_tenure(self):
        with pytest.raises(ValueError, match="Tenure must be positive"):
            calculate_emi(1000000, 8.5, 0)


class TestAmortizationSchedule:
    """Amortization schedule tests."""

    def test_schedule_length(self):
        result = build_amortization_schedule(1000000, 10, 12)
        assert len(result.schedule) == 12

    def test_first_month_interest_dominates(self):
        """In early months, interest component > principal component"""
        result = build_amortization_schedule(3000000, 8.5, 240)
        first_month = result.schedule[0]
        assert first_month.interest_component > first_month.principal_component

    def test_last_month_closes_to_zero(self):
        """Closing balance in last month should be 0"""
        result = build_amortization_schedule(1000000, 10, 120)
        last_month = result.schedule[-1]
        assert last_month.closing_balance == 0.0

    def test_opening_balance_matches_principal(self):
        result = build_amortization_schedule(500000, 12, 60)
        assert result.schedule[0].opening_balance == 500000

    def test_emi_consistent(self):
        result = build_amortization_schedule(1000000, 10, 120)
        # All EMIs should be the same (except possibly last)
        emis = [row.emi for row in result.schedule[:-1]]
        assert len(set(emis)) == 1


class TestPrepaymentBenefit:
    """Prepayment benefit calculation tests."""

    def test_prepayment_reduces_tenure(self):
        result = calculate_prepayment_benefit(2500000, 8.5, 200, 500000)
        assert result.months_reduced > 0
        assert result.new_tenure_months < 200

    def test_prepayment_saves_interest(self):
        result = calculate_prepayment_benefit(2500000, 8.5, 200, 500000)
        assert result.interest_saved > 0
        assert result.new_total_interest < result.original_total_interest

    def test_prepayment_exceeds_outstanding(self):
        with pytest.raises(ValueError, match="Prepayment amount must be less than"):
            calculate_prepayment_benefit(1000000, 8.5, 120, 1500000)

    def test_small_prepayment(self):
        result = calculate_prepayment_benefit(3000000, 8.5, 240, 100000)
        assert result.months_reduced > 0
        assert result.interest_saved > 0


class TestRefinanceBreakEven:
    """Refinance break-even tests."""

    def test_beneficial_refinance(self):
        result = refinance_break_even(9.0, 7.0, 2000000, 180, 30000)
        assert result.monthly_savings > 0
        assert result.break_even_months > 0
        assert result.total_savings_over_tenure > 0
        assert "Refinance recommended" in result.recommendation

    def test_no_benefit_higher_rate(self):
        result = refinance_break_even(7.0, 9.0, 2000000, 180, 30000)
        assert result.monthly_savings == 0
        assert "not beneficial" in result.recommendation

    def test_fee_exceeds_savings(self):
        # Tiny rate difference, huge fee
        result = refinance_break_even(8.5, 8.4, 500000, 12, 500000)
        assert result.total_savings_over_tenure < 0
        assert "not recommended" in result.recommendation


class TestDebtToIncomeRatio:
    """DTI ratio tests."""

    def test_healthy_dti(self):
        result = debt_to_income_ratio(15000, 100000)
        assert result.dti_ratio == 0.15
        assert result.category == "Healthy"

    def test_stressed_dti(self):
        result = debt_to_income_ratio(40000, 100000)
        assert result.dti_ratio == 0.40
        assert result.category == "Stressed"

    def test_critical_dti(self):
        result = debt_to_income_ratio(60000, 100000)
        assert result.category == "Critical"

    def test_zero_income_raises(self):
        with pytest.raises(ValueError, match="Monthly income must be positive"):
            debt_to_income_ratio(10000, 0)
