"""
ML Training Pipeline — XGBoost financial stress classifier.

Target: CV AUC ≥ 0.80
Uses SHAP TreeExplainer for top-3 factor attribution.
Logs to MLflow for experiment tracking.
"""

from __future__ import annotations

import os
import pickle
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.metrics import roc_auc_score, classification_report
from sklearn.model_selection import StratifiedKFold


def train_stress_model(
    data_path: str = "ml/data/synthetic_profiles.csv",
    model_output: str = "ml/models/stress_model.pkl",
    n_folds: int = 5,
) -> dict:
    """
    Train XGBoost stress classifier with StratifiedKFold CV.

    Args:
        data_path: Path to training data CSV
        model_output: Path to save trained model
        n_folds: Number of CV folds

    Returns:
        Dict with cv_auc, classification_report, feature_importances
    """
    from xgboost import XGBClassifier

    # Load data
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
    else:
        logger.info("Data not found — generating synthetic data")
        from ml.generate_data import generate_synthetic_data
        df = generate_synthetic_data(10000)

    feature_cols = [
        "monthly_income", "debt_to_income", "emergency_months",
        "equity_pct", "n_loans", "insurance_score", "age", "n_dependents",
    ]

    X = df[feature_cols].values
    y = df["is_stressed"].values

    logger.info(f"Training data: {X.shape[0]} samples, {X.shape[1]} features")
    logger.info(f"Class balance: {y.mean():.2%} stressed")

    # Stratified K-Fold CV
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
    cv_aucs = []

    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=(1 - y.mean()) / y.mean(),
        random_state=42,
        eval_metric="auc",
        use_label_encoder=False,
    )

    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

        y_pred_proba = model.predict_proba(X_val)[:, 1]
        fold_auc = roc_auc_score(y_val, y_pred_proba)
        cv_aucs.append(fold_auc)
        logger.info(f"Fold {fold + 1}/{n_folds}: AUC = {fold_auc:.4f}")

    mean_auc = np.mean(cv_aucs)
    std_auc = np.std(cv_aucs)
    logger.info(f"CV AUC: {mean_auc:.4f} ± {std_auc:.4f}")

    # Train final model on all data
    model.fit(X, y, verbose=False)

    # SHAP explanations
    shap_values = None
    explainer = None
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X[:100])  # Sample for speed
        logger.info("SHAP explainer created successfully")
    except ImportError:
        logger.warning("shap not installed — skipping SHAP analysis")
    except Exception as e:
        logger.warning(f"SHAP failed: {e}")

    # Feature importances
    importance = dict(zip(feature_cols, model.feature_importances_))
    sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    logger.info("Feature importances:")
    for feat, imp in sorted_importance:
        logger.info(f"  {feat}: {imp:.4f}")

    # Save model artifacts
    os.makedirs(os.path.dirname(model_output), exist_ok=True)
    artifacts = {
        "model": model,
        "feature_cols": feature_cols,
        "explainer": explainer,
        "cv_auc": mean_auc,
        "cv_std": std_auc,
    }
    with open(model_output, "wb") as f:
        pickle.dump(artifacts, f)
    logger.info(f"Model saved to {model_output}")

    # MLflow logging (optional)
    try:
        import mlflow
        mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000"))

        with mlflow.start_run(run_name="stress_model_xgboost"):
            mlflow.log_params({
                "n_estimators": 200,
                "max_depth": 6,
                "learning_rate": 0.1,
                "n_folds": n_folds,
                "n_samples": len(df),
            })
            mlflow.log_metrics({
                "cv_auc_mean": mean_auc,
                "cv_auc_std": std_auc,
            })
            for feat, imp in sorted_importance:
                mlflow.log_metric(f"importance_{feat}", imp)

            mlflow.log_artifact(model_output)
        logger.info("MLflow run logged")
    except Exception as e:
        logger.warning(f"MLflow logging skipped: {e}")

    # Classification report on full data
    y_pred = model.predict(X)
    report = classification_report(y, y_pred, output_dict=True)

    return {
        "cv_auc": mean_auc,
        "cv_std": std_auc,
        "feature_importances": sorted_importance,
        "classification_report": report,
        "model_path": model_output,
    }


def load_model(model_path: str = "ml/models/stress_model.pkl") -> dict:
    """Load trained model artifacts."""
    with open(model_path, "rb") as f:
        return pickle.load(f)


def predict_stress(profile: dict, model_path: str = "ml/models/stress_model.pkl") -> dict:
    """
    Predict financial stress for a single profile.

    Args:
        profile: Dict with feature values
        model_path: Path to saved model

    Returns:
        Dict with score, category, top_factors
    """
    artifacts = load_model(model_path)
    model = artifacts["model"]
    feature_cols = artifacts["feature_cols"]
    explainer = artifacts.get("explainer")

    X = np.array([[profile.get(col, 0) for col in feature_cols]])
    prob = float(model.predict_proba(X)[0, 1])
    score = round(prob * 100, 1)

    if score <= 30:
        category = "low"
    elif score <= 60:
        category = "medium"
    else:
        category = "high"

    # SHAP explanations
    top_factors = []
    if explainer:
        try:
            shap_vals = explainer.shap_values(X)[0]
            factor_impacts = list(zip(feature_cols, shap_vals))
            factor_impacts.sort(key=lambda x: abs(x[1]), reverse=True)
            for feat, impact in factor_impacts[:3]:
                top_factors.append({
                    "feature": feat,
                    "impact": round(float(abs(impact)), 4),
                    "direction": "increases_risk" if impact > 0 else "decreases_risk",
                })
        except Exception:
            pass

    if not top_factors:
        # Fallback: use feature importances
        importances = dict(zip(feature_cols, model.feature_importances_))
        sorted_imp = sorted(importances.items(), key=lambda x: x[1], reverse=True)
        for feat, imp in sorted_imp[:3]:
            top_factors.append({
                "feature": feat,
                "impact": round(float(imp), 4),
                "direction": "increases_risk",
            })

    return {
        "score": score,
        "category": category,
        "top_factors": top_factors,
        "disclaimer": "Educational decision support only. Not financial advice.",
    }


if __name__ == "__main__":
    result = train_stress_model()
    print(f"\n{'='*50}")
    print(f"CV AUC: {result['cv_auc']:.4f} ± {result['cv_std']:.4f}")
    print(f"Model saved to: {result['model_path']}")
    assert result["cv_auc"] >= 0.80, f"AUC {result['cv_auc']:.4f} < 0.80 target"
    print("✅ AUC target met!")
