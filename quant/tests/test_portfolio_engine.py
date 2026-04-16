"""
Tests for portfolio_engine.py
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from quant.portfolio_engine import (
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_var,
    net_worth,
)


class TestSharpeRatio:
    """Sharpe ratio calculation tests."""

    def test_positive_sharpe(self):
        """Returns consistently above risk-free → Sharpe > 0"""
        returns = [0.02, 0.015, 0.018, 0.022, 0.019, 0.021, 0.017, 0.023, 0.02, 0.018, 0.016, 0.02]
        result = calculate_sharpe_ratio(returns, risk_free_rate=0.065)
        assert result.sharpe_ratio > 0
        assert result.annualized_return > result.risk_free_rate

    def test_negative_sharpe(self):
        """Returns below risk-free → Sharpe < 0"""
        returns = [-0.01, -0.005, 0.002, -0.008, -0.012, 0.001, -0.003, -0.009, -0.006, 0.003, -0.007, -0.004]
        result = calculate_sharpe_ratio(returns, risk_free_rate=0.065)
        assert result.sharpe_ratio < 0

    def test_risk_free_rate_default(self):
        """Default risk-free rate should be 6.5% (India context)."""
        returns = [0.01] * 12
        result = calculate_sharpe_ratio(returns)
        assert result.risk_free_rate == 0.065

    def test_insufficient_data_raises(self):
        with pytest.raises(ValueError, match="at least 2"):
            calculate_sharpe_ratio([0.01])


class TestMaxDrawdown:
    """Max drawdown tests."""

    def test_known_drawdown(self):
        """Portfolio: 100 → 120 → 80 → 110 → drawdown = (80-120)/120 = 33.33%"""
        values = [100, 110, 120, 95, 80, 90, 100, 110]
        result = calculate_max_drawdown(values)
        assert abs(result.max_drawdown - 0.3333) < 0.01
        assert result.peak_value == 120
        assert result.trough_value == 80

    def test_no_drawdown(self):
        """Monotonically increasing → drawdown = 0"""
        values = [100, 110, 120, 130, 140, 150]
        result = calculate_max_drawdown(values)
        assert result.max_drawdown == 0.0

    def test_full_crash(self):
        """Portfolio drops to near 0"""
        values = [100, 90, 50, 10, 5, 8]
        result = calculate_max_drawdown(values)
        assert result.max_drawdown > 0.9

    def test_insufficient_data_raises(self):
        with pytest.raises(ValueError, match="at least 2"):
            calculate_max_drawdown([100])


class TestVaR:
    """Value at Risk tests."""

    def test_95_confidence(self):
        """VaR at 95% confidence should be positive for a portfolio with losses."""
        returns = [0.02, -0.03, 0.01, -0.05, 0.015, -0.02, 0.03, -0.01, 0.005, -0.04, 0.02, -0.015]
        result = calculate_var(returns, confidence=0.95)
        assert result.var_value > 0
        assert result.confidence == 0.95
        assert "95%" in result.interpretation

    def test_99_confidence_higher_than_95(self):
        """VaR at 99% should be higher than at 95%."""
        returns = [0.02, -0.03, 0.01, -0.05, 0.015, -0.02, 0.03, -0.01, 0.005, -0.04, 0.02, -0.015]
        var_95 = calculate_var(returns, confidence=0.95).var_value
        var_99 = calculate_var(returns, confidence=0.99).var_value
        assert var_99 > var_95

    def test_invalid_confidence_raises(self):
        with pytest.raises(ValueError, match="Confidence must be between"):
            calculate_var([0.01, -0.01], confidence=1.5)


class TestNetWorth:
    """Net worth calculation tests."""

    def test_positive_net_worth(self):
        assets = {"equity": 2000000, "real_estate": 5000000, "fd": 500000}
        liabilities = {"home_loan": 3000000, "car_loan": 500000}
        result = net_worth(assets, liabilities)
        assert result.net_worth == 4000000
        assert result.total_assets == 7500000
        assert result.total_liabilities == 3500000

    def test_negative_net_worth(self):
        assets = {"savings": 100000}
        liabilities = {"loans": 500000}
        result = net_worth(assets, liabilities)
        assert result.net_worth == -400000

    def test_no_liabilities(self):
        assets = {"equity": 1000000, "gold": 500000}
        liabilities = {}
        result = net_worth(assets, liabilities)
        assert result.net_worth == 1500000
        assert result.total_liabilities == 0

    def test_breakdown_preserved(self):
        assets = {"equity": 500000, "fd": 300000}
        liabilities = {"loan": 200000}
        result = net_worth(assets, liabilities)
        assert result.asset_breakdown == assets
        assert result.liability_breakdown == liabilities
