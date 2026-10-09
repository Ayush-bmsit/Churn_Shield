"""K-Means segmentation on numerical customer features.

Cluster names are derived from each cluster's average tenure and monthly charges
compared with overall medians. Names are descriptive, not value judgments
such as 'loyal' or 'valuable'.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from backend.config import settings

CLUSTER_FEATURES = ["tenure", "MonthlyCharges", "TotalCharges"]
N_CLUSTERS = 4


def _name_from_centroid(tenure: float, monthly: float, tenure_med: float, monthly_med: float) -> str:
    tenure_part = "Longer tenure" if tenure >= tenure_med else "Shorter tenure"
    spend_part = "higher monthly charges" if monthly >= monthly_med else "lower monthly charges"
    return f"{tenure_part}, {spend_part}"


def fit_and_label(df: pd.DataFrame, n_clusters: int = N_CLUSTERS) -> tuple[pd.DataFrame, dict]:
    work = df.copy()
    for col in CLUSTER_FEATURES:
        work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0)

    scaler = StandardScaler()
    X = scaler.fit_transform(work[CLUSTER_FEATURES])
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    work["cluster_id"] = labels

    tenure_med = float(work["tenure"].median())
    monthly_med = float(work["MonthlyCharges"].median())

    summary = {}
    names = {}
    for cluster_id in range(n_clusters):
        subset = work[work["cluster_id"] == cluster_id]
        centroid = {
            "count": int(len(subset)),
            "avg_tenure": float(subset["tenure"].mean()) if len(subset) else 0.0,
            "avg_monthly_charges": float(subset["MonthlyCharges"].mean()) if len(subset) else 0.0,
            "avg_total_charges": float(subset["TotalCharges"].mean()) if len(subset) else 0.0,
        }
        name = _name_from_centroid(
            centroid["avg_tenure"], centroid["avg_monthly_charges"], tenure_med, monthly_med
        )
        names[str(cluster_id)] = name
        centroid["segment_name"] = name
        summary[str(cluster_id)] = centroid
        work.loc[work["cluster_id"] == cluster_id, "segment_name"] = name

    models_dir = Path(settings.models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({"scaler": scaler, "kmeans": kmeans}, models_dir / "kmeans.joblib")
    payload = {
        "n_clusters": n_clusters,
        "features": CLUSTER_FEATURES,
        "naming_rule": (
            "Each cluster is named by comparing its mean tenure and mean MonthlyCharges "
            f"to the overall medians (tenure median={tenure_med:.1f}, "
            f"monthly median={monthly_med:.2f}). "
            "These labels describe usage patterns only."
        ),
        "clusters": summary,
        "medians": {"tenure": tenure_med, "MonthlyCharges": monthly_med},
    }
    (models_dir / "segment_names.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return work, payload
