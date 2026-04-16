"""
Simulation Engine — Monte Carlo simulations and stress testing.

Uses Geometric Brownian Motion for portfolio growth modeling.
All functions return typed Pydantic models.
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

from backend.app.schemas.models import JobLossStressResult, MonteCarloResult, SimulationPercentiles


def monte_carlo_portfolio_growth(
    initial_value: float,
    monthly_sip: float,
    annual_return_mean: float,
    annual_return_std: float,
    time_horizon_months: int,
    n_simulations: int = 10000,
    seed: int | None = None,
) -> MonteCarloResult:
    """
    Run Monte Carlo simulation of portfolio growth using Geometric Brownian Motion.

    Each simulation path:
    1. Starts with initial_value
    2. Each month: value = value * exp((mu - sigma^2/2)*dt + sigma*sqrt(dt)*Z) + monthly_sip
       where Z ~ N(0,1), mu = annual return, sigma = annual volatility, dt = 1/12

    Args:
        initial_value: Starting portfolio value
        monthly_sip: Monthly systematic investment amount
        annual_return_mean: Expected annual return (e.g., 0.12 for 12%)
        annual_return_std: Annual return standard deviation (e.g., 0.18 for 18%)
        time_horizon_months: Investment horizon in months
        n_simulations: Number of simulation paths (default 10,000)
        seed: Random seed for reproducibility (optional)

    Returns:
        MonteCarloResult with P10/P50/P90 percentiles and monthly value paths
    """
    if initial_value < 0:
        raise ValueError("Initial value cannot be negative")
    if time_horizon_months <= 0:
        raise ValueError("Time horizon must be positive")

    rng = np.random.default_rng(seed)

    dt = 1.0 / 12.0
    mu = annual_return_mean
    sigma = annual_return_std

    # Pre-compute drift and diffusion
    drift = (mu - 0.5 * sigma**2) * dt
    diffusion = sigma * np.sqrt(dt)

    # Generate all random shocks at once: shape (n_simulations, time_horizon_months)
    shocks = rng.standard_normal((n_simulations, time_horizon_months))

    # Initialize portfolio values matrix
    values = np.zeros((n_simulations, time_horizon_months + 1))
    values[:, 0] = initial_value

    # Vectorized simulation
    for t in range(time_horizon_months):
        monthly_return = np.exp(drift + diffusion * shocks[:, t])
        values[:, t + 1] = values[:, t] * monthly_return + monthly_sip

    # Extract final values
    final_values = values[:, -1]

    # Compute percentiles of final value
    p10, p50, p90 = np.percentile(final_values, [10, 50, 90])

    # Compute monthly percentile paths for charting
    monthly_p10 = np.percentile(values, 10, axis=0).tolist()
    monthly_p50 = np.percentile(values, 50, axis=0).tolist()
    monthly_p90 = np.percentile(values, 90, axis=0).tolist()

    return MonteCarloResult(
        initial_value=initial_value,
        monthly_sip=monthly_sip,
        time_horizon_months=time_horizon_months,
        n_simulations=n_simulations,
        annual_return_mean=annual_return_mean,
        annual_return_std=annual_return_std,
        final_value=SimulationPercentiles(
            p10=round(float(p10), 2),
            p50=round(float(p50), 2),
            p90=round(float(p90), 2),
        ),
        monthly_values_p10=[round(v, 2) for v in monthly_p10],
        monthly_values_p50=[round(v, 2) for v in monthly_p50],
        monthly_values_p90=[round(v, 2) for v in monthly_p90],
    )


def job_loss_stress_test(
    monthly_expenses: float,
    emergency_fund: float,
    income_loss_months: int,
    additional_income: float = 0.0,
) -> JobLossStressResult:
    """
    Stress-test financial survival during income loss (job loss, career break).

    Simulates month-by-month fund depletion considering:
    - Fixed monthly expenses
    - Any additional income (freelance, passive income)
    - Emergency fund as the only buffer

    Args:
        monthly_expenses: Total monthly expenses
        emergency_fund: Available emergency fund
        income_loss_months: Duration of income loss in months
        additional_income: Any remaining income during the period (default 0)

    Returns:
        JobLossStressResult with survival assessment and depletion schedule
    """
    if monthly_expenses <= 0:
        raise ValueError("Monthly expenses must be positive")
    if emergency_fund < 0:
        raise ValueError("Emergency fund cannot be negative")
    if income_loss_months <= 0:
        raise ValueError("Income loss months must be positive")

    net_monthly_burn = monthly_expenses - additional_income
    if net_monthly_burn <= 0:
        # Additional income covers expenses — survives indefinitely
        return JobLossStressResult(
            monthly_expenses=monthly_expenses,
            emergency_fund=emergency_fund,
            income_loss_months=income_loss_months,
            months_of_runway=float(income_loss_months),
            survives=True,
            shortfall=0.0,
            depletion_schedule=[emergency_fund] * (income_loss_months + 1),
        )

    # Calculate months of runway
    months_of_runway = emergency_fund / net_monthly_burn

    # Build depletion schedule
    depletion_schedule: list[float] = [round(emergency_fund, 2)]
    balance = emergency_fund
    for _ in range(income_loss_months):
        balance = max(0.0, balance - net_monthly_burn)
        depletion_schedule.append(round(balance, 2))

    survives = months_of_runway >= income_loss_months
    shortfall = max(0.0, (net_monthly_burn * income_loss_months) - emergency_fund)

    return JobLossStressResult(
        monthly_expenses=monthly_expenses,
        emergency_fund=emergency_fund,
        income_loss_months=income_loss_months,
        months_of_runway=round(months_of_runway, 2),
        survives=survives,
        shortfall=round(shortfall, 2),
        depletion_schedule=depletion_schedule,
    )
