"""Rule-based retention suggestions.

The churn model only estimates risk. These actions are hand-written business
rules for the prototype, not learned by the model.
"""

from backend.ml.preprocessing import HIGH_RISK_MIN


def retention_suggestions(features: dict, churn_probability: float) -> list[str]:
    contract = str(features.get("Contract") or "")
    tenure = int(features.get("tenure") or 0)
    monthly = float(features.get("MonthlyCharges") or 0)
    tech = str(features.get("TechSupport") or "")
    internet = str(features.get("InternetService") or "")

    suggestions: list[str] = []
    high = churn_probability > HIGH_RISK_MIN

    if high and contract == "Month-to-month":
        suggestions.append(
            "High risk + month-to-month contract: consider a longer-term contract offer."
        )
    if high and tenure < 6:
        suggestions.append(
            "High risk + short tenure: consider onboarding or support intervention."
        )
    if high and monthly >= 70:
        suggestions.append(
            "High risk + high monthly charges: consider reviewing plan/value concerns."
        )
    if high and tech == "No" and internet in {"DSL", "Fiber optic"}:
        suggestions.append(
            "High risk + internet without tech support: consider a support add-on offer."
        )
    if not suggestions and high:
        suggestions.append(
            "High risk, but no specific contract/tenure/price rule matched. Review the account manually."
        )
    if not suggestions:
        suggestions.append(
            "No high-priority retention rule triggered. Continue routine monitoring."
        )

    return suggestions
