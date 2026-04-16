"""
Comparator — NPV-based financial decision comparison.

Compares two cashflow streams using Net Present Value analysis.
All functions return typed Pydantic models.
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from scipy.optimize import brentq

from backend.app.schemas.models import NPVComparisonResult


def _calculate_npv(cashflows: list[float], discount_rate: float) -> float:
    """
    Calculate Net Present Value of a cashflow stream.

    NPV = sum( cashflow_t / (1 + r)^t ) for t = 0, 1, ..., n

    Args:
        cashflows: List of cashflows (index 0 = period 0)
        discount_rate: Periodic discount rate as decimal

    Returns:
        NPV as float
    """
    periods = np.arange(len(cashflows))
    discount_factors = (1 + discount_rate) ** periods
    return float(np.sum(np.array(cashflows) / discount_factors))


def npv_comparison(
    cashflows_a: list[float],
    cashflows_b: list[float],
    discount_rate: float,
    label_a: str = "Option A",
    label_b: str = "Option B",
) -> NPVComparisonResult:
    """
    Compare two cashflow streams using NPV analysis.

    Also attempts to find the break-even discount rate where both options
    have equal NPV (if one exists).

    Args:
        cashflows_a: Cashflow stream for option A
        cashflows_b: Cashflow stream for option B
        discount_rate: Annual discount rate as decimal (e.g., 0.08 for 8%)
        label_a: Label for option A
        label_b: Label for option B

    Returns:
        NPVComparisonResult with NPVs, winner, and break-even return rate
    """
    if not cashflows_a or not cashflows_b:
        raise ValueError("Cashflow lists cannot be empty")

    # Pad shorter list with zeros
    max_len = max(len(cashflows_a), len(cashflows_b))
    cf_a = cashflows_a + [0.0] * (max_len - len(cashflows_a))
    cf_b = cashflows_b + [0.0] * (max_len - len(cashflows_b))

    # Monthly discount rate if discount_rate is annual
    monthly_rate = discount_rate / 12

    npv_a = _calculate_npv(cf_a, monthly_rate)
    npv_b = _calculate_npv(cf_b, monthly_rate)

    winner = label_a if npv_a >= npv_b else label_b
    difference = abs(npv_a - npv_b)

    # Find break-even return rate
    break_even_return = None
    try:
        diff_cashflows = [a - b for a, b in zip(cf_a, cf_b)]

        def npv_diff(rate: float) -> float:
            return _calculate_npv(diff_cashflows, rate / 12)

        # Search between 0.1% and 50% annual rate
        if npv_diff(0.001) * npv_diff(0.50) < 0:
            be = brentq(npv_diff, 0.001, 0.50, xtol=1e-6)
            break_even_return = round(float(be), 6)
    except (ValueError, RuntimeError):
        # No break-even found in range — that's fine
        pass

    return NPVComparisonResult(
        npv_a=round(npv_a, 2),
        npv_b=round(npv_b, 2),
        label_a=label_a,
        label_b=label_b,
        winner=winner,
        difference=round(difference, 2),
        break_even_return=break_even_return,
    )
