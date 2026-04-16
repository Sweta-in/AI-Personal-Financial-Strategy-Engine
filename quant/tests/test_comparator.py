"""
Tests for comparator.py — NPV comparison engine.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from quant.comparator import npv_comparison


class TestNPVComparison:
    """NPV comparison tests."""

    def test_prepay_vs_invest_scenario(self):
        """
        Scenario: ₹5L lump sum
        Option A (Prepay): saves monthly interest over 120 months
        Option B (Invest): earns returns over 120 months
        """
        # Simplified: Option A saves ₹3,541/month for 120 months
        cashflows_a = [-500000] + [3541] * 120

        # Option B earns ~1% monthly on ₹5L compounding
        cashflows_b = [-500000] + [0] * 119 + [500000 * (1.01) ** 120]

        result = npv_comparison(cashflows_a, cashflows_b, 0.08, "Prepay Loan", "Invest in MF")
        assert result.winner in ("Prepay Loan", "Invest in MF")
        assert result.difference > 0
        assert result.label_a == "Prepay Loan"
        assert result.label_b == "Invest in MF"

    def test_identical_cashflows(self):
        """Same cashflows → NPVs should be equal, difference ≈ 0."""
        cf = [-100000, 20000, 20000, 20000, 20000, 20000]
        result = npv_comparison(cf, cf, 0.10)
        assert abs(result.difference) < 1

    def test_clear_winner(self):
        """One option clearly dominates."""
        cf_a = [-100000, 30000, 30000, 30000, 30000]
        cf_b = [-100000, 10000, 10000, 10000, 10000]
        result = npv_comparison(cf_a, cf_b, 0.10, "Good Deal", "Bad Deal")
        assert result.winner == "Good Deal"
        assert result.npv_a > result.npv_b

    def test_different_length_cashflows(self):
        """Shorter cashflow is padded with zeros."""
        cf_a = [-100000, 50000, 50000, 50000]
        cf_b = [-100000, 30000, 30000, 30000, 30000, 30000]
        result = npv_comparison(cf_a, cf_b, 0.08)
        # Should work without error
        assert result.npv_a is not None
        assert result.npv_b is not None

    def test_empty_cashflows_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            npv_comparison([], [100], 0.1)
