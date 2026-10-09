"""Offline training script. Not exposed as an HTTP endpoint.

Compares Logistic Regression, Random Forest, and XGBoost (if installed).
Saves one sklearn Pipeline (preprocessor + chosen model) so inference
reuses the exact same transformations.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.ml.preprocessing import (  # noqa: E402
    CATEGORICAL_FEATURES,
    FEATURE_COLUMNS,
    ID_COL,
    NUMERIC_FEATURES,
    TARGET_COL,
    clean_features,
)


def _build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
        ]
    )


def _candidate_models(y_train: pd.Series) -> dict:
    neg = int((y_train == 0).sum())
    pos = int((y_train == 1).sum())
    scale_pos = (neg / pos) if pos else 1.0
    models = {
        "logistic_regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "random_forest": RandomForestClassifier(
            n_estimators=200,
            
            class_weight="balanced",
            n_jobs=-1,
        ),
    }
    try:
        from xgboost import XGBClassifier

        models["xgboost"] = XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            scale_pos_weight=scale_pos,
            eval_metric="logloss",
            n_jobs=-1,
        )
    except Exception as exc:
        print(f"XGBoost not available, skipping: {exc}")
    return models


def _metrics(y_true, y_pred, y_proba) -> dict:
    return {
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_proba)),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }


def train(csv_path: str | Path | None = None, models_dir: str | Path | None = None) -> dict:
    csv_path = Path(csv_path or ROOT / "data" / "WA_Fn-UseC_-Telco-Customer-Churn.csv")
    models_dir = Path(models_dir or ROOT / "models")
    models_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path)
    df = clean_features(df)
    df = df.dropna(subset=FEATURE_COLUMNS + [TARGET_COL])
    y = (df[TARGET_COL].astype(str).str.strip().str.lower() == "yes").astype(int)
    X = df[FEATURE_COLUMNS]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y
    )

    results = {}
    fitted = {}
    for name, clf in _candidate_models(y_train).items():
        pipe = Pipeline(
            steps=[
                ("preprocess", _build_preprocessor()),
                ("model", clf),
            ]
        )
        pipe.fit(X_train, y_train)
        proba = pipe.predict_proba(X_test)[:, 1]
        pred = (proba >= 0.5).astype(int)
        results[name] = _metrics(y_test, pred, proba)
        fitted[name] = pipe
        print(name, results[name])

    # Prototype selection: highest test ROC-AUC. This is NOT a claim that the
    # model is universally best — it is the best among these candidates on this split.
    selected_name = max(results, key=lambda n: results[n]["roc_auc"])
    selected_pipeline = fitted[selected_name]

    preprocessor = selected_pipeline.named_steps["preprocess"]
    feature_names = list(preprocessor.get_feature_names_out())
    X_train_transformed = preprocessor.transform(X_train)
    rng = np.random.default_rng(42)
    sample_size = min(100, len(X_train_transformed))
    idx = rng.choice(len(X_train_transformed), size=sample_size, replace=False)
    background = np.asarray(X_train_transformed[idx])

    joblib.dump(selected_pipeline, models_dir / "churn_pipeline.joblib")
    np.save(models_dir / "shap_background.npy", background)
    payload = {
        "selected_model": selected_name,
        "selection_rule": "highest roc_auc on the held-out 20% test split",
        "metrics": results,
        "feature_names": feature_names,
        "feature_columns": FEATURE_COLUMNS,
        "id_column": ID_COL,
        "notes": (
            "Metrics are from one train/test split. They are for this prototype only "
            "and should not be treated as a production benchmark."
        ),
    }
    (models_dir / "training_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Selected model: {selected_name}")
    return payload


if __name__ == "__main__":
    train()
