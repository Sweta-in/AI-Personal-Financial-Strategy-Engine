"""
ML model tests.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ml.generate_data import generate_synthetic_data


class TestDataGeneration:
    def test_correct_shape(self):
        df = generate_synthetic_data(1000, seed=42)
        assert df.shape == (1000, 9)

    def test_feature_ranges(self):
        df = generate_synthetic_data(5000, seed=42)
        assert df["monthly_income"].min() >= 20000
        assert df["monthly_income"].max() <= 1000000
        assert df["debt_to_income"].min() >= 0
        assert df["debt_to_income"].max() <= 0.8
        assert df["emergency_months"].min() >= 0
        assert df["age"].min() >= 22
        assert df["age"].max() <= 60
        assert df["n_dependents"].min() >= 0

    def test_label_balance(self):
        df = generate_synthetic_data(10000, seed=42)
        stress_rate = df["is_stressed"].mean()
        # Should be between 20-60% stressed
        assert 0.15 < stress_rate < 0.65

    def test_deterministic(self):
        df1 = generate_synthetic_data(100, seed=123)
        df2 = generate_synthetic_data(100, seed=123)
        assert df1.equals(df2)


class TestModelTraining:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.data_path = str(tmp_path / "test_data.csv")
        self.model_path = str(tmp_path / "test_model.pkl")
        df = generate_synthetic_data(2000, seed=42)
        df.to_csv(self.data_path, index=False)

    def test_training_completes(self):
        try:
            from ml.train import train_stress_model
            result = train_stress_model(
                data_path=self.data_path,
                model_output=self.model_path,
                n_folds=3,
            )
            assert result["cv_auc"] > 0.5  # Better than random
            assert os.path.exists(self.model_path)
        except ImportError:
            pytest.skip("xgboost not installed")

    def test_auc_threshold(self):
        try:
            from ml.train import train_stress_model
            result = train_stress_model(
                data_path=self.data_path,
                model_output=self.model_path,
                n_folds=5,
            )
            assert result["cv_auc"] >= 0.75, f"AUC {result['cv_auc']:.4f} below threshold"
        except ImportError:
            pytest.skip("xgboost not installed")

    def test_prediction(self):
        try:
            from ml.train import train_stress_model, predict_stress
            train_stress_model(
                data_path=self.data_path,
                model_output=self.model_path,
                n_folds=3,
            )
            result = predict_stress({
                "monthly_income": 100000,
                "debt_to_income": 0.3,
                "emergency_months": 6,
                "equity_pct": 0.4,
                "n_loans": 2,
                "insurance_score": 0.8,
                "age": 35,
                "n_dependents": 1,
            }, model_path=self.model_path)

            assert 0 <= result["score"] <= 100
            assert result["category"] in ("low", "medium", "high")
            assert len(result["top_factors"]) == 3
        except ImportError:
            pytest.skip("xgboost not installed")
