"""
Tests for simulation_engine.py
"""

import time

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from quant.simulation_engine import job_loss_stress_test, monte_carlo_portfolio_growth


class TestMonteCarloPortfolioGrowth:
    """Monte Carlo simulation tests."""

    def test_basic_simulation(self):
        """10,000 simulations should complete and return valid structure."""
        result = monte_carlo_portfolio_growth(
            initial_value=1000000,
            monthly_sip=25000,
            annual_return_mean=0.12,
            annual_return_std=0.18,
            time_horizon_months=120,
            n_simulations=10000,
            seed=42,
        )
        assert result.n_simulations == 10000
        assert result.time_horizon_months == 120
        assert len(result.monthly_values_p50) == 121  # 0 to 120 inclusive
        assert result.final_value.p10 > 0
        assert result.final_value.p50 > result.final_value.p10
        assert result.final_value.p90 > result.final_value.p50

    def test_performance_under_2_seconds(self):
        """10,000 paths must complete in < 2 seconds."""
        start = time.time()
        monte_carlo_portfolio_growth(
            initial_value=1000000,
            monthly_sip=25000,
            annual_return_mean=0.12,
            annual_return_std=0.18,
            time_horizon_months=120,
            n_simulations=10000,
            seed=42,
        )
        elapsed = time.time() - start
        assert elapsed < 2.0, f"Monte Carlo took {elapsed:.2f}s — must be under 2s"

    def test_deterministic_with_seed(self):
        """Same seed should produce identical results."""
        kwargs = dict(
            initial_value=500000,
            monthly_sip=10000,
            annual_return_mean=0.10,
            annual_return_std=0.15,
            time_horizon_months=60,
            n_simulations=1000,
            seed=123,
        )
        r1 = monte_carlo_portfolio_growth(**kwargs)
        r2 = monte_carlo_portfolio_growth(**kwargs)
        assert r1.final_value.p50 == r2.final_value.p50

    def test_zero_sip(self):
        """No SIP — only initial investment grows."""
        result = monte_carlo_portfolio_growth(
            initial_value=1000000,
            monthly_sip=0,
            annual_return_mean=0.10,
            annual_return_std=0.15,
            time_horizon_months=60,
            n_simulations=5000,
            seed=42,
        )
        # Median should be roughly around initial * exp(0.10 * 5)
        assert result.final_value.p50 > 1000000

    def test_high_volatility(self):
        """High volatility widens the P10/P90 spread."""
        low_vol = monte_carlo_portfolio_growth(
            initial_value=1000000, monthly_sip=0, annual_return_mean=0.10,
            annual_return_std=0.10, time_horizon_months=120, n_simulations=5000, seed=42,
        )
        high_vol = monte_carlo_portfolio_growth(
            initial_value=1000000, monthly_sip=0, annual_return_mean=0.10,
            annual_return_std=0.30, time_horizon_months=120, n_simulations=5000, seed=42,
        )
        low_spread = low_vol.final_value.p90 - low_vol.final_value.p10
        high_spread = high_vol.final_value.p90 - high_vol.final_value.p10
        assert high_spread > low_spread

    def test_negative_initial_raises(self):
        with pytest.raises(ValueError):
            monte_carlo_portfolio_growth(-100, 0, 0.1, 0.1, 12)

    def test_zero_horizon_raises(self):
        with pytest.raises(ValueError):
            monte_carlo_portfolio_growth(100000, 0, 0.1, 0.1, 0)


class TestJobLossStressTest:
    """Job loss stress test cases."""

    def test_survives_with_sufficient_fund(self):
        result = job_loss_stress_test(
            monthly_expenses=50000,
            emergency_fund=500000,
            income_loss_months=6,
        )
        assert result.survives is True
        assert result.shortfall == 0.0
        assert result.months_of_runway == 10.0

    def test_fails_with_insufficient_fund(self):
        result = job_loss_stress_test(
            monthly_expenses=50000,
            emergency_fund=100000,
            income_loss_months=6,
        )
        assert result.survives is False
        assert result.shortfall > 0
        assert result.months_of_runway == 2.0

    def test_depletion_schedule_length(self):
        result = job_loss_stress_test(
            monthly_expenses=30000,
            emergency_fund=200000,
            income_loss_months=8,
        )
        # Schedule has income_loss_months + 1 entries (initial + each month)
        assert len(result.depletion_schedule) == 9

    def test_depletion_never_negative(self):
        result = job_loss_stress_test(
            monthly_expenses=50000,
            emergency_fund=100000,
            income_loss_months=12,
        )
        assert all(v >= 0 for v in result.depletion_schedule)

    def test_additional_income_helps(self):
        without = job_loss_stress_test(50000, 200000, 6, additional_income=0)
        with_income = job_loss_stress_test(50000, 200000, 6, additional_income=20000)
        assert with_income.months_of_runway > without.months_of_runway

    def test_income_covers_expenses(self):
        """If additional income >= expenses, survives indefinitely."""
        result = job_loss_stress_test(
            monthly_expenses=30000,
            emergency_fund=50000,
            income_loss_months=12,
            additional_income=35000,
        )
        assert result.survives is True
        assert result.shortfall == 0.0
