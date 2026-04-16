"""
Synthetic data generation for financial stress prediction model.

Creates 10,000 synthetic financial profiles with stress labels.
Features: monthly_income, debt_to_income, emergency_months, equity_pct,
          n_loans, insurance_score, age, n_dependents
Label: is_stressed (binary)
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from loguru import logger


def generate_synthetic_data(n_samples: int = 10000, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic financial profiles with stress labels.

    Stress probability formula:
    p(stress) = sigmoid(
        2.0 * (dti - 0.3)
        + 1.5 * (1 / (emergency_months + 0.1) - 0.3)
        + 0.8 * (equity_pct - 0.5)
        + 0.5 * (n_loans / 5)
        + 1.0 * (1 - insurance_score)
        - 0.3 * (monthly_income / 200000)
        + 0.4 * (n_dependents / 3)
        + 0.2 * ((age - 35) / 20)
        + noise
    )

    Args:
        n_samples: Number of samples to generate
        seed: Random seed for reproducibility

    Returns:
        DataFrame with features and is_stressed label
    """
    rng = np.random.default_rng(seed)

    # Generate features with realistic Indian distributions
    monthly_income = rng.lognormal(mean=11.2, sigma=0.6, size=n_samples)  # ₹50K-₹5L range
    monthly_income = np.clip(monthly_income, 20000, 1000000)

    debt_to_income = rng.beta(2, 5, size=n_samples)  # Skewed low
    debt_to_income = np.clip(debt_to_income, 0, 0.8)

    emergency_months = rng.exponential(scale=6, size=n_samples)
    emergency_months = np.clip(emergency_months, 0, 36)

    equity_pct = rng.beta(3, 3, size=n_samples)  # Centered around 0.5

    n_loans = rng.poisson(lam=1.5, size=n_samples)
    n_loans = np.clip(n_loans, 0, 8)

    insurance_score = rng.beta(4, 2, size=n_samples)  # Skewed toward good coverage
    insurance_score = np.clip(insurance_score, 0, 1)

    age = rng.normal(loc=35, scale=8, size=n_samples).astype(int)
    age = np.clip(age, 22, 60)

    n_dependents = rng.poisson(lam=1.2, size=n_samples)
    n_dependents = np.clip(n_dependents, 0, 5)

    # Compute stress probability using logistic formula
    noise = rng.normal(0, 0.3, size=n_samples)

    logit = (
        2.0 * (debt_to_income - 0.3)
        + 1.5 * (1.0 / (emergency_months + 0.1) - 0.3)
        + 0.8 * (equity_pct - 0.5)
        + 0.5 * (n_loans / 5)
        + 1.0 * (1 - insurance_score)
        - 0.3 * (monthly_income / 200000)
        + 0.4 * (n_dependents / 3)
        + 0.2 * ((age - 35) / 20)
        + noise
    )

    stress_prob = 1 / (1 + np.exp(-logit))
    is_stressed = (rng.random(n_samples) < stress_prob).astype(int)

    df = pd.DataFrame({
        "monthly_income": np.round(monthly_income, 2),
        "debt_to_income": np.round(debt_to_income, 4),
        "emergency_months": np.round(emergency_months, 2),
        "equity_pct": np.round(equity_pct, 4),
        "n_loans": n_loans.astype(int),
        "insurance_score": np.round(insurance_score, 4),
        "age": age.astype(int),
        "n_dependents": n_dependents.astype(int),
        "is_stressed": is_stressed,
    })

    logger.info(f"Generated {n_samples} profiles. Stress rate: {is_stressed.mean():.2%}")
    return df


def save_data(df: pd.DataFrame, output_path: str = "ml/data/synthetic_profiles.csv"):
    """Save generated data to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} profiles to {output_path}")


if __name__ == "__main__":
    df = generate_synthetic_data(10000)
    save_data(df)
    print(f"\nClass distribution:\n{df['is_stressed'].value_counts()}")
    print(f"\nFeature statistics:\n{df.describe()}")
