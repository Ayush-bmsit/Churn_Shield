"""Load the saved sklearn Pipeline and score customers. Do not re-implement encoding here."""

import json
from pathlib import Path

import joblib
import pandas as pd

from backend.config import settings
from backend.ml.preprocessing import (
    FEATURE_COLUMNS,
    ID_COL,
    TEMPLATE_COLUMNS,
    clean_features,
    predicted_label,
    risk_level,
)

_pipeline = None


def models_dir() -> Path:
    return Path(settings.models_dir)


def pipeline_path() -> Path:
    return models_dir() / "churn_pipeline.joblib"


def load_pipeline():
    global _pipeline
    if _pipeline is None:
        path = pipeline_path()
        if not path.exists():
            raise FileNotFoundError(
                f"No trained pipeline at {path}. Run: python -m backend.ml.train"
            )
        _pipeline = joblib.load(path)
    return _pipeline


def reload_pipeline() -> None:
    global _pipeline
    _pipeline = None
    load_pipeline()


def decision_threshold() -> float:
    path = models_dir() / "training_metrics.json"
    if not path.exists():
        return 0.5
    payload = json.loads(path.read_text(encoding="utf-8"))
    return float(payload.get("decision_threshold", 0.5))


def predict_frame(df: pd.DataFrame) -> pd.DataFrame:
    pipe = load_pipeline()
    work = clean_features(df)
    missing = [c for c in FEATURE_COLUMNS if c not in work.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    X = work[FEATURE_COLUMNS]
    proba = pipe.predict_proba(X)[:, 1]
    threshold = decision_threshold()
    out = work.copy()
    if ID_COL not in out.columns:
        out[ID_COL] = [f"row-{i}" for i in range(len(out))]
    out["churn_probability"] = proba.round(4)
    out["predicted_churn"] = [predicted_label(p, threshold) for p in proba]
    out["risk_level"] = [risk_level(p) for p in proba]
    out["decision_threshold"] = threshold
    return out


def predict_one(feature_dict: dict) -> dict:
    df = pd.DataFrame([feature_dict])
    scored = predict_frame(df).iloc[0]
    return {
        "customerID": str(scored.get(ID_COL, "")),
        "churn_probability": float(scored["churn_probability"]),
        "predicted_churn": str(scored["predicted_churn"]),
        "risk_level": str(scored["risk_level"]),
        "decision_threshold": float(scored["decision_threshold"]),
    }


def template_columns() -> list[str]:
    return list(TEMPLATE_COLUMNS)
