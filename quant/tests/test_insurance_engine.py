"""
Tests for insurance_engine.py
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from quant.insurance_engine import (
    health_insurance_sufficiency,
    insurance_adequacy_score,
    required_term_coverage,
)


class TestRequiredTermCoverage:
    """HLV-based term coverage tests."""

    def test_young_professional_with_dependents(self):
        """30-year-old earning ₹12L/year with 2 dependents and ₹30L loans"""
        result = required_term_coverage(
            annual_income=1200000,
            age=30,
            dependents=2,
            outstanding_loans=3000000,
        )
        assert result.method == "HLV"
        assert result.required_coverage > 10000000  # Should be > ₹1Cr
        assert result.income_replacement_component > 0
        assert result.loan_coverage_component == 3000000

    def test_older_professional_lower_coverage(self):
        """55-year-old needs less coverage than 30-year-old (same income)."""
        young = required_term_coverage(1200000, 30, 2, 0)
        older = required_term_coverage(1200000, 55, 2, 0)
        assert young.required_coverage > older.required_coverage

    def test_more_dependents_higher_coverage(self):
        """More dependents → higher coverage."""
        no_deps = required_term_coverage(1200000, 35, 0, 0)
        with_deps = required_term_coverage(1200000, 35, 3, 0)
        assert with_deps.required_coverage > no_deps.required_coverage

    def test_loans_add_to_coverage(self):
        """Outstanding loans are added directly to coverage."""
        no_loan = required_term_coverage(1200000, 35, 1, 0)
        with_loan = required_term_coverage(1200000, 35, 1, 5000000)
        assert with_loan.required_coverage - no_loan.required_coverage == 5000000

    def test_invalid_age_raises(self):
        with pytest.raises(ValueError, match="Age must be between"):
            required_term_coverage(1000000, 15, 0, 0)

    def test_retirement_age_worker(self):
        """At age 60, working years = 0, so income replacement = 0."""
        result = required_term_coverage(1200000, 60, 1, 1000000)
        assert result.income_replacement_component == 0
        assert result.required_coverage == 1000000  # Only loans


class TestInsuranceAdequacyScore:
    """Insurance adequacy scoring tests."""

    def test_adequate_coverage(self):
        result = insurance_adequacy_score(10000000, 8000000)
        assert result.is_adequate is True
        assert result.adequacy_pct > 100

    def test_underinsured(self):
        result = insurance_adequacy_score(3000000, 10000000)
        assert result.is_adequate is False
        assert result.gap == 7000000
        assert "UNDERINSURED" in result.recommendation

    def test_critically_underinsured(self):
        result = insurance_adequacy_score(1000000, 10000000)
        assert "CRITICALLY UNDERINSURED" in result.recommendation

    def test_zero_requirement(self):
        result = insurance_adequacy_score(5000000, 0)
        assert result.is_adequate is True
        assert result.gap == 0


class TestHealthInsuranceSufficiency:
    """Health insurance sufficiency tests."""

    def test_tier1_city(self):
        result = health_insurance_sufficiency(500000, 35, 2, city_tier=1)
        assert result.recommended_cover >= 2000000  # ₹10L base + ₹5L x 2 deps
        assert result.is_sufficient is False

    def test_sufficient_coverage(self):
        result = health_insurance_sufficiency(3000000, 30, 1, city_tier=2)
        assert result.is_sufficient is True

    def test_older_person_needs_more(self):
        young = health_insurance_sufficiency(1500000, 25, 0, city_tier=1)
        older = health_insurance_sufficiency(1500000, 55, 0, city_tier=1)
        assert older.recommended_cover > young.recommended_cover

    def test_invalid_tier_defaults_to_1(self):
        result = health_insurance_sufficiency(1000000, 30, 0, city_tier=5)
        assert result.recommended_cover == 1000000  # Tier 1 base
