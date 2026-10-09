"""Domain features shared by the notebook, training, and inference.

Cutoffs are fixed in advance. They are not quantiles learned from data,
so computing them does not use the target and does not need a train-only fit.
"""

from __future__ import annotations

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from backend.ml.preprocessing import CATEGORICAL_FEATURES, FEATURE_COLUMNS, NUMERIC_FEATURES

# Internet add-ons only. "Yes" means the customer has that add-on.
# "No" and "No internet service" both count as zero: the add-on is not active.
# MultipleLines is excluded because it describes phone lines, not these add-ons.
OPTIONAL_SERVICE_COLUMNS = [
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
]

# 0 isolates brand-new accounts. 12 and 24 match the one-year and two-year
# contract lengths in this dataset. 48 marks a longer-tenure band past the
# longest standard contract. These are business labels, not optimized bins.
TENURE_GROUP_BINS = [-0.01, 0, 12, 24, 48, 10_000]
TENURE_GROUP_LABELS = [
    "0 months",
    "1-12 months",
    "13-24 months",
    "25-48 months",
    "49+ months",
]

ENGINEERED_NUMERIC = NUMERIC_FEATURES + ["optional_service_count"]
ENGINEERED_CATEGORICAL = CATEGORICAL_FEATURES + ["tenure_group"]


def tenure_group(tenure: pd.Series) -> pd.Series:
    values = pd.to_numeric(tenure, errors="coerce")
    grouped = pd.cut(
        values,
        bins=TENURE_GROUP_BINS,
        labels=TENURE_GROUP_LABELS,
        include_lowest=True,
    )
    labels = grouped.astype(object)
    labels = labels.where(values.notna(), "unknown")
    return labels.astype(str)


def optional_service_count(frame: pd.DataFrame) -> pd.Series:
    missing = [column for column in OPTIONAL_SERVICE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Cannot count optional services; missing columns: {missing}")
    count = pd.Series(0, index=frame.index, dtype=int)
    for column in OPTIONAL_SERVICE_COLUMNS:
        active = frame[column].astype(str).str.strip().str.lower().eq("yes")
        count = count + active.astype(int)
    return count


def add_domain_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with tenure_group and optional_service_count appended."""
    out = frame.copy()
    out["tenure_group"] = tenure_group(out["tenure"]) if "tenure" in out.columns else "unknown"
    out["optional_service_count"] = optional_service_count(out)
    return out


class DomainFeatureAdder(BaseEstimator, TransformerMixin):
    """Deterministic feature step. fit does not look at y or learn statistics."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        if isinstance(X, pd.DataFrame):
            frame = X.copy()
        else:
            frame = pd.DataFrame(X, columns=FEATURE_COLUMNS)
        return add_domain_features(frame)


def columns_for(feature_config: str) -> tuple[list[str], list[str]]:
    if feature_config == "baseline":
        return list(NUMERIC_FEATURES), list(CATEGORICAL_FEATURES)
    if feature_config == "engineered":
        return list(ENGINEERED_NUMERIC), list(ENGINEERED_CATEGORICAL)
    raise ValueError(f"Unknown feature configuration: {feature_config}")


def feature_definitions() -> dict:
    return {
        "excluded_from_predictors": ["customerID", "Churn"],
        "baseline_numeric": list(NUMERIC_FEATURES),
        "baseline_categorical": list(CATEGORICAL_FEATURES),
        "engineered_additions": {
            "tenure_group": {
                "bins": TENURE_GROUP_BINS,
                "labels": TENURE_GROUP_LABELS,
                "purpose": (
                    "Represent early-life, contract-length, and longer-tenure stages "
                    "with fixed cutoffs so a linear model can treat them as categories."
                ),
            },
            "optional_service_count": {
                "columns": OPTIONAL_SERVICE_COLUMNS,
                "rule": "Count values equal to Yes. No and No internet service count as 0.",
                "excluded": ["MultipleLines", "PhoneService"],
                "purpose": "Summarise how many listed internet add-ons are active.",
            },
        },
    }
