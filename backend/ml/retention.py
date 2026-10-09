"""Retention text derived from the synthetic policy rules.

The churn model only estimates risk. Offer eligibility is not learned from data.
"""

from backend.ml.decision_support import build_decision


def retention_suggestions(
    features: dict,
    churn_probability: float,
    decision_threshold: float = 0.5,
    explanation_ok: bool = True,
) -> list[str]:
    decision = build_decision(
        features,
        churn_probability,
        decision_threshold=decision_threshold,
        explanation_ok=explanation_ok,
    )
    return decision["messages"]
