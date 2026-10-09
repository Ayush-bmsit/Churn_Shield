from pathlib import Path

import pytest

from backend.ml.explain import explain_one
from backend.ml.predict import predict_one

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "models" / "churn_pipeline.joblib"


pytestmark = pytest.mark.skipif(not PIPELINE.exists(), reason="saved pipeline is not present")


def _customer():
    return {
        "customerID": "unit-1",
        "gender": "Female",
        "SeniorCitizen": 0,
        "Partner": "No",
        "Dependents": "No",
        "tenure": 2,
        "PhoneService": "Yes",
        "MultipleLines": "No",
        "InternetService": "Fiber optic",
        "OnlineSecurity": "No",
        "OnlineBackup": "No",
        "DeviceProtection": "No",
        "TechSupport": "No",
        "StreamingTV": "No",
        "StreamingMovies": "No",
        "Contract": "Month-to-month",
        "PaperlessBilling": "Yes",
        "PaymentMethod": "Electronic check",
        "MonthlyCharges": 80.0,
        "TotalCharges": 160.0,
    }


def test_saved_pipeline_scores_raw_columns():
    scored = predict_one(_customer())
    assert 0.0 <= scored["churn_probability"] <= 1.0
    assert scored["predicted_churn"] in {"Yes", "No"}
    assert scored["risk_level"] in {"Low", "Medium", "High"}
    assert "decision_threshold" in scored


def test_saved_pipeline_shap_returns_factors_or_a_clear_error():
    explanation = explain_one(_customer())
    assert "ok" in explanation
    if explanation["ok"]:
        assert explanation["factors"]
        assert "cause" in explanation["note"].lower() or "not causes" in explanation["note"]
    else:
        assert explanation["error"]
