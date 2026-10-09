"""Leakage-safe model comparison for the IBM telco churn CSV.

The final test split is created first and is not used to rank models,
compare feature sets, or choose the decision threshold.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from backend.ml.features import DomainFeatureAdder, columns_for, feature_definitions
from backend.ml.preprocessing import FEATURE_COLUMNS, TARGET_COL, clean_features

RANDOM_STATE = 42
TEST_SIZE = 0.2
N_SPLITS = 5
# Fixed settings so every candidate is comparable. This is not a search.
TREE_ROUNDS = 80

ROOT = Path(__file__).resolve().parents[2]


def load_clean_frame(csv_path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(csv_path)
    return clean_features(frame)


def encode_target(frame: pd.DataFrame) -> pd.Series:
    return frame[TARGET_COL].astype(str).str.strip().str.lower().eq("yes").astype(int)


def split_development_test(
    features: pd.DataFrame,
    target: pd.Series,
    test_size: float = TEST_SIZE,
    random_state: int = RANDOM_STATE,
):
    return train_test_split(
        features,
        target,
        test_size=test_size,
        stratify=target,
        random_state=random_state,
    )


def make_cv(random_state: int = RANDOM_STATE) -> StratifiedKFold:
    return StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=random_state)


def build_preprocessor(feature_config: str) -> ColumnTransformer:
    numeric, categorical = columns_for(feature_config)
    numeric_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, numeric),
            ("cat", categorical_pipe, categorical),
        ]
    )


def _positive_weight(y: pd.Series) -> float:
    positive = int((y == 1).sum())
    negative = int((y == 0).sum())
    if positive == 0:
        return 1.0
    return float(negative / positive)


def _boosting_models(scale_pos_weight: float) -> dict:
    models = {}
    try:
        from xgboost import XGBClassifier

        models["xgboost"] = XGBClassifier(
            n_estimators=TREE_ROUNDS,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.9,
            colsample_bytree=0.9,
            scale_pos_weight=scale_pos_weight,
            eval_metric="logloss",
            random_state=RANDOM_STATE,
            n_jobs=1,
        )
    except Exception as exc:
        print(f"XGBoost unavailable: {exc}")
    try:
        from lightgbm import LGBMClassifier

        models["lightgbm"] = LGBMClassifier(
            n_estimators=TREE_ROUNDS,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.9,
            colsample_bytree=0.9,
            scale_pos_weight=scale_pos_weight,
            random_state=RANDOM_STATE,
            n_jobs=1,
            verbose=-1,
        )
    except Exception as exc:
        print(f"LightGBM unavailable: {exc}")
    try:
        from catboost import CatBoostClassifier

        models["catboost"] = CatBoostClassifier(
            iterations=TREE_ROUNDS,
            depth=4,
            learning_rate=0.1,
            scale_pos_weight=scale_pos_weight,
            loss_function="Logloss",
            random_seed=RANDOM_STATE,
            verbose=0,
            allow_writing_files=False,
        )
    except Exception as exc:
        print(f"CatBoost unavailable: {exc}")
    return models


def available_estimators(y_train: pd.Series, imbalance: str) -> dict:
    """Build unfitted estimators.

    imbalance:
    - class_weight: balanced logistic/forest, and scale_pos_weight for boosters
    - none: no class weight and scale_pos_weight of 1
    """
    if imbalance not in {"class_weight", "none"}:
        raise ValueError(imbalance)
    weighted = imbalance == "class_weight"
    scale = _positive_weight(y_train) if weighted else 1.0
    models = {
        "logistic_regression": LogisticRegression(
            max_iter=1000,
            class_weight="balanced" if weighted else None,
            random_state=RANDOM_STATE,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=TREE_ROUNDS,
            max_depth=12,
            min_samples_leaf=5,
            class_weight="balanced" if weighted else None,
            random_state=RANDOM_STATE,
            n_jobs=1,
        ),
    }
    models.update(_boosting_models(scale))
    return models


def build_estimator(feature_config: str, estimator, imbalance: str = "class_weight"):
    steps: list = []
    if feature_config == "engineered":
        steps.append(("domain_features", DomainFeatureAdder()))
    steps.append(("preprocess", build_preprocessor(feature_config)))
    if imbalance == "smote":
        from imblearn.over_sampling import SMOTE
        from imblearn.pipeline import Pipeline as ImbPipeline

        steps.append(("smote", SMOTE(random_state=RANDOM_STATE)))
        steps.append(("model", estimator))
        return ImbPipeline(steps)
    steps.append(("model", estimator))
    return Pipeline(steps)


def _score_fold(y_true, proba) -> dict:
    pred = (proba >= 0.5).astype(int)
    return {
        "average_precision": float(average_precision_score(y_true, proba)),
        "roc_auc": float(roc_auc_score(y_true, proba)),
        "precision_at_0_50": float(precision_score(y_true, pred, zero_division=0)),
        "recall_at_0_50": float(recall_score(y_true, pred, zero_division=0)),
        "f1_at_0_50": float(f1_score(y_true, pred, zero_division=0)),
        "brier": float(brier_score_loss(y_true, proba)),
    }


def cross_validate_estimator(estimator, features: pd.DataFrame, target: pd.Series, cv) -> dict:
    folds = []
    for train_index, valid_index in cv.split(features, target):
        candidate = clone(estimator)
        candidate.fit(features.iloc[train_index], target.iloc[train_index])
        proba = candidate.predict_proba(features.iloc[valid_index])[:, 1]
        folds.append(_score_fold(target.iloc[valid_index], proba))
    summary = {"folds": folds}
    for key in folds[0]:
        values = np.array([fold[key] for fold in folds], dtype=float)
        summary[f"{key}_mean"] = float(values.mean())
        summary[f"{key}_std"] = float(values.std(ddof=1))
    return summary


def choose_threshold(y_true, proba) -> dict:
    """Pick the threshold with the highest F1 on the supplied labels only."""
    y_true = np.asarray(y_true)
    proba = np.asarray(proba)
    best = None
    rows = []
    for threshold in np.round(np.arange(0.05, 0.96, 0.01), 2):
        pred = (proba >= threshold).astype(int)
        row = {
            "threshold": float(threshold),
            "precision": float(precision_score(y_true, pred, zero_division=0)),
            "recall": float(recall_score(y_true, pred, zero_division=0)),
            "f1": float(f1_score(y_true, pred, zero_division=0)),
            "flagged": int(pred.sum()),
            "flagged_rate": float(pred.mean()),
            "false_positives": int(((pred == 1) & (y_true == 0)).sum()),
            "false_negatives": int(((pred == 0) & (y_true == 1)).sum()),
        }
        rows.append(row)
        if best is None or row["f1"] > best["f1"] or (
            row["f1"] == best["f1"] and row["threshold"] < best["threshold"]
        ):
            best = row
    return {"policy": "maximize F1 on out-of-fold development probabilities", "selected": best, "curve": rows}


def classification_report_dict(y_true, proba, threshold: float) -> dict:
    pred = (np.asarray(proba) >= threshold).astype(int)
    y_true = np.asarray(y_true)
    return {
        "threshold": float(threshold),
        "average_precision": float(average_precision_score(y_true, proba)),
        "roc_auc": float(roc_auc_score(y_true, proba)),
        "precision": float(precision_score(y_true, pred, zero_division=0)),
        "recall": float(recall_score(y_true, pred, zero_division=0)),
        "f1": float(f1_score(y_true, pred, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, pred)),
        "brier": float(brier_score_loss(y_true, proba)),
        "confusion_matrix": confusion_matrix(y_true, pred).tolist(),
        "flagged": int(pred.sum()),
        "flagged_rate": float(pred.mean()),
    }


def transform_for_shap(pipeline, features: pd.DataFrame) -> np.ndarray:
    data = features
    for name, step in pipeline.steps[:-1]:
        if name == "smote":
            continue
        data = step.transform(data)
    return np.asarray(data)


def _candidate_specs(y_development: pd.Series) -> list[dict]:
    specs = []
    weighted = available_estimators(y_development, "class_weight")
    unweighted = available_estimators(y_development, "none")
    for feature_config in ("baseline", "engineered"):
        for name, estimator in weighted.items():
            specs.append(
                {
                    "feature_config": feature_config,
                    "model": name,
                    "imbalance": "class_weight",
                    "estimator": estimator,
                }
            )
        if "logistic_regression" in unweighted:
            specs.append(
                {
                    "feature_config": feature_config,
                    "model": "logistic_regression",
                    "imbalance": "none",
                    "estimator": unweighted["logistic_regression"],
                }
            )
        if "lightgbm" in unweighted:
            specs.append(
                {
                    "feature_config": feature_config,
                    "model": "lightgbm",
                    "imbalance": "none",
                    "estimator": unweighted["lightgbm"],
                }
            )
        try:
            from imblearn.over_sampling import SMOTE  # noqa: F401

            specs.append(
                {
                    "feature_config": feature_config,
                    "model": "logistic_regression",
                    "imbalance": "smote",
                    "estimator": unweighted["logistic_regression"],
                }
            )
        except Exception as exc:
            print(f"SMOTE unavailable: {exc}")
        ensemble = _soft_vote(weighted)
        if ensemble is not None:
            specs.append(
                {
                    "feature_config": feature_config,
                    "model": "soft_vote_xgb_cat_lgbm",
                    "imbalance": "class_weight",
                    "estimator": ensemble,
                }
            )
    return specs


def _soft_vote(models: dict):
    members = []
    for name in ("xgboost", "catboost", "lightgbm"):
        if name in models:
            members.append((name, models[name]))
    if len(members) < 3:
        print("Soft-voting ensemble skipped because XGBoost, CatBoost, and LightGBM are not all available.")
        return None
    return VotingClassifier(estimators=members, voting="soft")


def _single_split_ranking(features: pd.DataFrame, target: pd.Series) -> list[dict]:
    """Diagnostic ranking on one development split. Not used for selection.

    The candidates are the class-weighted models, including the soft vote when
    it can be built. Unweighted and SMOTE runs stay in the cross-validation table.
    """
    x_fit, x_hold, y_fit, y_hold = train_test_split(
        features,
        target,
        test_size=0.2,
        stratify=target,
        random_state=RANDOM_STATE,
    )
    rows = []
    weighted = available_estimators(y_fit, "class_weight")
    specs = [(name, estimator) for name, estimator in weighted.items()]
    ensemble = _soft_vote(weighted)
    if ensemble is not None:
        specs.append(("soft_vote_xgb_cat_lgbm", ensemble))
    for feature_config in ("baseline", "engineered"):
        for name, estimator in specs:
            pipeline = build_estimator(feature_config, estimator, "class_weight")
            pipeline.fit(x_fit, y_fit)
            proba = pipeline.predict_proba(x_hold)[:, 1]
            rows.append(
                {
                    "feature_config": feature_config,
                    "model": name,
                    "imbalance": "class_weight",
                    "holdout_roc_auc": float(roc_auc_score(y_hold, proba)),
                    "holdout_average_precision": float(average_precision_score(y_hold, proba)),
                }
            )
    rows.sort(key=lambda row: row["holdout_roc_auc"], reverse=True)
    return rows


def run_experiments(
    csv_path: str | Path | None = None,
    models_dir: str | Path | None = None,
    save: bool = True,
) -> dict:
    csv_path = Path(csv_path or ROOT / "data" / "WA_Fn-UseC_-Telco-Customer-Churn.csv")
    models_dir = Path(models_dir or ROOT / "models")
    frame = load_clean_frame(csv_path)
    target = encode_target(frame)
    features = frame[FEATURE_COLUMNS].copy()
    x_dev, x_test, y_dev, y_test = split_development_test(features, target)
    cv = make_cv()

    rows = []
    fitted_specs = []
    for spec in _candidate_specs(y_dev):
        label = f"{spec['feature_config']} | {spec['model']} | {spec['imbalance']}"
        print(f"Cross-validating {label}")
        try:
            pipeline = build_estimator(spec["feature_config"], spec["estimator"], spec["imbalance"])
            summary = cross_validate_estimator(pipeline, x_dev, y_dev, cv)
        except Exception as exc:
            print(f"Skipped {label}: {exc}")
            rows.append(
                {
                    "feature_config": spec["feature_config"],
                    "model": spec["model"],
                    "imbalance": spec["imbalance"],
                    "error": str(exc),
                }
            )
            continue
        row = {
            "feature_config": spec["feature_config"],
            "model": spec["model"],
            "imbalance": spec["imbalance"],
            "average_precision_mean": summary["average_precision_mean"],
            "average_precision_std": summary["average_precision_std"],
            "roc_auc_mean": summary["roc_auc_mean"],
            "roc_auc_std": summary["roc_auc_std"],
            "precision_at_0_50_mean": summary["precision_at_0_50_mean"],
            "recall_at_0_50_mean": summary["recall_at_0_50_mean"],
            "f1_at_0_50_mean": summary["f1_at_0_50_mean"],
            "f1_at_0_50_std": summary["f1_at_0_50_std"],
            "brier_mean": summary["brier_mean"],
            "folds": summary["folds"],
        }
        rows.append(row)
        fitted_specs.append(spec)
        print(
            f"  AP {row['average_precision_mean']:.4f} ± {row['average_precision_std']:.4f} "
            f"ROC-AUC {row['roc_auc_mean']:.4f}"
        )

    successful = [row for row in rows if "average_precision_mean" in row]
    if not successful:
        raise RuntimeError("No model finished cross-validation.")
    selected = max(successful, key=lambda row: (row["average_precision_mean"], -row["average_precision_std"]))
    selected_spec = next(
        spec
        for spec in fitted_specs
        if spec["feature_config"] == selected["feature_config"]
        and spec["model"] == selected["model"]
        and spec["imbalance"] == selected["imbalance"]
    )

    print("Ranking a single development split by ROC-AUC (diagnostic only).")
    single_split = _single_split_ranking(x_dev, y_dev)
    single_winner = single_split[0]

    print("Collecting out-of-fold probabilities for threshold selection.")
    oof = np.zeros(len(y_dev), dtype=float)
    for train_index, valid_index in cv.split(x_dev, y_dev):
        candidate = build_estimator(
            selected_spec["feature_config"],
            clone(selected_spec["estimator"]),
            selected_spec["imbalance"],
        )
        candidate.fit(x_dev.iloc[train_index], y_dev.iloc[train_index])
        oof[valid_index] = candidate.predict_proba(x_dev.iloc[valid_index])[:, 1]
    threshold_report = choose_threshold(y_dev, oof)
    threshold = float(threshold_report["selected"]["threshold"])
    oof_metrics = classification_report_dict(y_dev, oof, threshold)

    print("Fitting the selected pipeline on the full development set.")
    final_pipeline = build_estimator(
        selected_spec["feature_config"],
        clone(selected_spec["estimator"]),
        selected_spec["imbalance"],
    )
    final_pipeline.fit(x_dev, y_dev)
    test_proba = final_pipeline.predict_proba(x_test)[:, 1]
    test_metrics = classification_report_dict(y_test, test_proba, threshold)

    transformed = transform_for_shap(final_pipeline, x_dev)
    rng = np.random.default_rng(RANDOM_STATE)
    sample_size = min(100, len(transformed))
    background = transformed[rng.choice(len(transformed), size=sample_size, replace=False)]
    preprocess = final_pipeline.named_steps["preprocess"]
    feature_names = list(preprocess.get_feature_names_out())

    payload = {
        "selected_model": selected["model"],
        "selected_feature_config": selected["feature_config"],
        "selected_imbalance": selected["imbalance"],
        "selection_rule": (
            "Highest mean stratified 5-fold average precision on the development set. "
            "The 20% test set was not used for feature, model, or threshold selection."
        ),
        "decision_threshold": threshold,
        "threshold_policy": threshold_report["policy"],
        "threshold_selection": threshold_report["selected"],
        "oof_metrics_at_selected_threshold": oof_metrics,
        "final_test_metrics": test_metrics,
        "cv_results": rows,
        "single_development_split_roc_auc_ranking": single_split,
        "single_split_would_select": single_winner,
        "feature_definitions": feature_definitions(),
        "feature_names": feature_names,
        "feature_columns": FEATURE_COLUMNS,
        "random_state": RANDOM_STATE,
        "test_size": TEST_SIZE,
        "n_splits": N_SPLITS,
        "hyperparameters": {
            "note": "Fixed comparable settings. No inner search was run.",
            "tree_rounds": TREE_ROUNDS,
        },
        "notes": (
            "Precision, recall, and F1 inside cv_results use a 0.50 cutoff and are descriptive. "
            "The deployed cutoff is decision_threshold, chosen from out-of-fold development scores. "
            "final_test_metrics is the only test-set evaluation."
        ),
    }

    if save:
        models_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(final_pipeline, models_dir / "churn_pipeline.joblib")
        np.save(models_dir / "shap_background.npy", background)
        (models_dir / "training_metrics.json").write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        print(
            f"Saved {selected['feature_config']} / {selected['model']} / {selected['imbalance']} "
            f"with threshold {threshold:.2f}"
        )
    payload["threshold_curve"] = threshold_report["curve"]
    return payload
