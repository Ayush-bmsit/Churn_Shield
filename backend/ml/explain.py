"""SHAP explanations using the saved pipeline's preprocessor + model.

Explanations are computed from SHAP values, not invented text.
If SHAP cannot run for the fitted model, a clear error is returned.
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap

from backend.config import settings
from backend.ml.preprocessing import FEATURE_COLUMNS, clean_features


def _human_label(transformed_name: str) -> str:
    name = transformed_name
    if name.startswith("num__"):
        name = name[len("num__") :]
    if name.startswith("cat__"):
        name = name[len("cat__") :]
    return name.replace("_", " ")


def explain_one(feature_dict: dict, top_n: int = 5) -> dict:
    models_dir = Path(settings.models_dir)
    pipeline = joblib.load(models_dir / "churn_pipeline.joblib")
    preprocess = pipeline.named_steps["preprocess"]
    model = pipeline.named_steps["model"]

    df = clean_features(pd.DataFrame([feature_dict]))
    X = df[FEATURE_COLUMNS]
    Xt = np.asarray(preprocess.transform(X))
    feature_names = list(preprocess.get_feature_names_out())

    model_name = type(model).__name__.lower()
    shap_values = None
    method = ""

    try:
        if "logistic" in model_name:
            background = np.load(models_dir / "shap_background.npy")
            if len(background) > 100:
                background = background[:100]
            explainer = shap.LinearExplainer(model, background)
            shap_values = np.asarray(explainer.shap_values(Xt))
            method = "shap.LinearExplainer"
        else:
            explainer = shap.TreeExplainer(model)
            raw = explainer.shap_values(Xt)
            method = "shap.TreeExplainer"
            if isinstance(raw, list):
                shap_values = np.asarray(raw[1] if len(raw) > 1 else raw[0])
            else:
                shap_values = np.asarray(raw)
                if shap_values.ndim == 3:
                    shap_values = shap_values[:, :, 1]
    except Exception as exc:
        return {
            "ok": False,
            "error": (
                f"SHAP could not explain this model ({type(model).__name__}): {exc}. "
                "Predictions still come from the saved pipeline; only the explanation is unavailable."
            ),
            "factors": [],
            "method": method or "failed",
        }

    row = shap_values[0]
    order = np.argsort(np.abs(row))[::-1]
    factors = []
    for idx in order[:top_n]:
        value = float(row[idx])
        if abs(value) < 1e-9:
            continue
        direction = "increases predicted churn risk" if value > 0 else "decreases predicted churn risk"
        factors.append(
            {
                "feature": feature_names[idx],
                "label": _human_label(feature_names[idx]),
                "shap_value": round(value, 4),
                "effect": direction,
            }
        )

    return {
        "ok": True,
        "method": method,
        "model_type": type(model).__name__,
        "factors": factors,
        "note": "Positive SHAP values push the prediction toward churn (class Yes).",
    }
