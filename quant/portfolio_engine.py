"""
Portfolio Engine — Portfolio analytics and net worth computation.

Calculates Sharpe ratio, max drawdown, VaR, and net worth.
All functions return typed Pydantic models.
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

from backend.app.schemas.models import MaxDrawdownResult, NetWorthResult, SharpeRatioResult, VaRResult


def calculate_sharpe_ratio(
    returns: list[float],
    risk_free_rate: float = 0.065,
) -> SharpeRatioResult:
    """
    Calculate the annualized Sharpe ratio from a series of periodic returns.

    Sharpe = (annualized_return - risk_free_rate) / annualized_volatility

    Assumes returns are monthly. Annualizes by:
    - Return: (1 + mean_monthly)^12 - 1
    - Volatility: monthly_std * sqrt(12)

    Args:
        returns: List of periodic (monthly) returns as decimals (e.g., 0.02 for 2%)
        risk_free_rate: Annual risk-free rate (default 6.5% for India)

    Returns:
        SharpeRatioResult with Sharpe ratio and component values
    """
    if len(returns) < 2:
        raise ValueError("Need at least 2 return observations")

    returns_arr = np.array(returns)
    mean_monthly = float(np.mean(returns_arr))
    std_monthly = float(np.std(returns_arr, ddof=1))

    # Annualize
    annualized_return = (1 + mean_monthly) ** 12 - 1
    annualized_volatility = std_monthly * np.sqrt(12)

    if annualized_volatility == 0:
        sharpe = 0.0
    else:
        sharpe = (annualized_return - risk_free_rate) / annualized_volatility

    return SharpeRatioResult(
        sharpe_ratio=round(float(sharpe), 4),
        annualized_return=round(annualized_return, 4),
        annualized_volatility=round(annualized_volatility, 4),
        risk_free_rate=risk_free_rate,
    )


def calculate_max_drawdown(portfolio_values: list[float]) -> MaxDrawdownResult:
    """
    Calculate maximum drawdown (peak-to-trough decline) of a portfolio.

    Max Drawdown = (trough - peak) / peak

    Args:
        portfolio_values: Time series of portfolio values

    Returns:
        MaxDrawdownResult with drawdown percentage and peak/trough details
    """
    if len(portfolio_values) < 2:
        raise ValueError("Need at least 2 portfolio values")

    values = np.array(portfolio_values)
    running_max = np.maximum.accumulate(values)
    drawdowns = (values - running_max) / running_max

    trough_idx = int(np.argmin(drawdowns))
    peak_idx = int(np.argmax(values[:trough_idx + 1]))

    max_dd = float(drawdowns[trough_idx])

    return MaxDrawdownResult(
        max_drawdown=round(abs(max_dd), 4),
        peak_value=round(float(values[peak_idx]), 2),
        trough_value=round(float(values[trough_idx]), 2),
        peak_index=peak_idx,
        trough_index=trough_idx,
    )


def calculate_var(
    returns: list[float],
    confidence: float = 0.95,
) -> VaRResult:
    """
    Calculate parametric Value at Risk (VaR) assuming normal distribution.

    VaR = -(mean - z_score * std)

    Args:
        returns: List of periodic returns as decimals
        confidence: Confidence level (default 0.95 = 95%)

    Returns:
        VaRResult with VaR value and interpretation
    """
    if len(returns) < 2:
        raise ValueError("Need at least 2 return observations")
    if not 0 < confidence < 1:
        raise ValueError("Confidence must be between 0 and 1")

    from scipy import stats

    returns_arr = np.array(returns)
    mean_ret = float(np.mean(returns_arr))
    std_ret = float(np.std(returns_arr, ddof=1))

    z_score = stats.norm.ppf(1 - confidence)
    var_value = -(mean_ret + z_score * std_ret)

    interpretation = (
        f"With {confidence*100:.0f}% confidence, the maximum expected loss "
        f"in a single period is {var_value*100:.2f}% of portfolio value."
    )

    return VaRResult(
        var_value=round(float(var_value), 6),
        confidence=confidence,
        interpretation=interpretation,
    )


def net_worth(
    assets: dict[str, float],
    liabilities: dict[str, float],
) -> NetWorthResult:
    """
    Calculate net worth with detailed breakdown.

    Args:
        assets: Dictionary of asset name → value
        liabilities: Dictionary of liability name → value

    Returns:
        NetWorthResult with total net worth and breakdowns
    """
    total_assets = sum(assets.values())
    total_liabilities = sum(liabilities.values())
    nw = total_assets - total_liabilities

    return NetWorthResult(
        total_assets=round(total_assets, 2),
        total_liabilities=round(total_liabilities, 2),
        net_worth=round(nw, 2),
        asset_breakdown=assets,
        liability_breakdown=liabilities,
    )
