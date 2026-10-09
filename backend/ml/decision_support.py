"""Map a score to a synthetic Northwind Mobile retention action.

The numeric limits are the same ones written in data/mock_company_policies.
This module does not retrieve documents. It applies those rules directly.
"""

from __future__ import annotations

LOW_RISK_MAX = 0.30
HIGH_RISK_MIN = 0.70
MAX_DISCOUNT_PERCENT = 15
MAX_DURATION_MONTHS = 3
EMPLOYEE_MONTHLY_AUTHORITY_FCU = 8.0
PER_CUSTOMER_MONTHLY_CAP_FCU = 25.0
MONTHLY_RETENTION_BUDGET_FCU = 25000

OFFER_DOC = "retention_offer_policy.md"
SEGMENT_DOC = "customer_segment_policy.md"
FINANCE_DOC = "finance_and_budget_policy.md"
COMMUNICATION_DOC = "customer_communication_policy.md"
CONTRACT_DOC = "contract_and_service_policy.md"
ESCALATION_DOC = "retention_escalation_matrix.md"


def _source(document: str, section: str) -> dict:
    return {"document": document, "section": section}


def _monthly_amount(monthly_charges: float, percent: float) -> float:
    raw = monthly_charges * percent / 100.0
    return round(min(raw, PER_CUSTOMER_MONTHLY_CAP_FCU), 2)


def build_decision(
    features: dict,
    churn_probability: float,
    decision_threshold: float = 0.5,
    explanation_ok: bool = True,
) -> dict:
    probability = float(churn_probability)
    threshold = float(decision_threshold)
    contract = str(features.get("Contract") or "")
    tenure = int(features.get("tenure") or 0)
    monthly = float(features.get("MonthlyCharges") or 0)
    tech = str(features.get("TechSupport") or "")
    internet = str(features.get("InternetService") or "")
    flagged = probability >= threshold
    if probability < LOW_RISK_MAX:
        risk = "Low"
    elif probability <= HIGH_RISK_MIN:
        risk = "Medium"
    else:
        risk = "High"

    sources = [
        _source(SEGMENT_DOC, "2. Risk handling"),
        _source(COMMUNICATION_DOC, "2. Contact limits"),
    ]
    messages: list[str] = []
    offer = {
        "tier": None,
        "discount_percent": 0,
        "duration_months": 0,
        "monthly_discount_fcu": 0.0,
        "eligible": False,
        "approval": "not_offered",
        "capped_at_25_fcu": False,
    }

    manual_review = (not explanation_ok) and risk == "High"
    if manual_review:
        sources.append(_source(ESCALATION_DOC, "3. Uncertain explanations"))

    if not flagged:
        messages.append(
            "Do not start retention outreach. The probability is below the saved decision threshold. "
            f"See {SEGMENT_DOC} section 2."
        )
        approval_reason = "below_decision_threshold"
    elif risk == "Low":
        messages.append(
            "The customer is flagged at the decision threshold but the risk bucket is Low. "
            f"No discount is allowed. Continue routine monitoring ({SEGMENT_DOC} section 2)."
        )
        approval_reason = "low_risk_bucket"
    elif contract == "Two year":
        messages.append(
            "No price discount. A two-year contract is outside the offer tiers "
            f"({OFFER_DOC} section 4.5)."
        )
        approval_reason = "two_year_contract"
        sources.append(_source(OFFER_DOC, "4.5 Ineligible cases"))
    else:
        eligible = []
        if (
            contract == "Month-to-month"
            and risk in {"Medium", "High"}
            and tenure >= 6
            and monthly >= 40
        ):
            eligible.append(("A", 5, 3, "4.1 Tier A"))
        if (
            contract == "Month-to-month"
            and risk == "High"
            and tenure >= 3
            and monthly >= 50
        ):
            eligible.append(("B", 10, 3, "4.2 Tier B"))
        if (
            risk == "High"
            and contract == "Month-to-month"
            and tenure < 12
            and internet == "Fiber optic"
            and tech == "No"
            and not manual_review
        ):
            eligible.append(("C", 15, 2, "4.3 Tier C"))
        if contract == "One year" and risk == "High" and tenure >= 6 and flagged:
            eligible.append(("A-exception", 5, 3, "4.4 One-year exception"))

        if not eligible:
            messages.append(
                "No discount tier matches this customer. "
                f"See {OFFER_DOC} sections 4.1 to 4.5."
            )
            approval_reason = "no_matching_tier"
            sources.append(_source(OFFER_DOC, "4. Offer tiers"))
        else:
            tier, percent, months, section = sorted(eligible, key=lambda item: item[1])[-1]
            amount = _monthly_amount(monthly, percent)
            capped = round(monthly * percent / 100.0, 2) > PER_CUSTOMER_MONTHLY_CAP_FCU
            manager = (
                tier in {"C", "A-exception"}
                or amount > EMPLOYEE_MONTHLY_AUTHORITY_FCU
                or manual_review
            )
            offer.update(
                {
                    "tier": tier,
                    "discount_percent": percent,
                    "duration_months": months,
                    "monthly_discount_fcu": amount,
                    "eligible": True,
                    "approval": "manager" if manager else "employee",
                    "capped_at_25_fcu": capped,
                }
            )
            approval_reason = "manager_required" if manager else "within_employee_authority"
            sources.append(_source(OFFER_DOC, section))
            sources.append(_source(FINANCE_DOC, "3. Authority and caps"))
            messages.append(
                f"Suggested offer: tier {tier}, {percent}% of monthly charges for {months} months "
                f"({amount:.2f} FCU per month). Approval: {offer['approval']}. "
                f"Source: {OFFER_DOC} {section}; {FINANCE_DOC} section 3."
            )
    if manual_review:
        messages.append(
            "SHAP factors are unavailable, so a high-risk recommendation is not final. "
            f"A manager must review the account ({ESCALATION_DOC} section 3). "
            "Tier C is not offered automatically in that case."
        )

    support_addon = (
        flagged
        and risk in {"Medium", "High"}
        and tech == "No"
        and internet in {"DSL", "Fiber optic"}
        and offer["tier"] != "C"
    )
    if support_addon:
        messages.append(
            "Non-discount option: one complimentary month of tech support. "
            f"An employee may offer this without a price change ({CONTRACT_DOC} section 3)."
        )
        sources.append(_source(CONTRACT_DOC, "3. Tech-support add-on"))

    messages.append(
        "Contact history is not stored in this prototype. Check the last 30 days before sending anything. "
        f"Maximum two outbound contacts ({COMMUNICATION_DOC} section 2)."
    )
    messages.append(
        "The monthly retention budget is 25,000 FCU, but this prototype does not track spend. "
        f"Budget headroom is unverified ({FINANCE_DOC} section 2)."
    )
    messages.append(
        "The churn score is a prediction. The offer is a synthetic policy match. "
        "Neither one shows that a discount will stop churn, and SHAP values are not causes."
    )

    return {
        "risk_level": risk,
        "flagged_for_outreach": flagged,
        "decision_threshold": threshold,
        "approval_reason": approval_reason,
        "offer": offer,
        "manual_review": manual_review,
        "support_addon": support_addon,
        "policy_sources": sources,
        "messages": messages,
        "limits": {
            "max_discount_percent": MAX_DISCOUNT_PERCENT,
            "max_duration_months": MAX_DURATION_MONTHS,
            "employee_monthly_authority_fcu": EMPLOYEE_MONTHLY_AUTHORITY_FCU,
            "per_customer_monthly_cap_fcu": PER_CUSTOMER_MONTHLY_CAP_FCU,
            "monthly_retention_budget_fcu": MONTHLY_RETENTION_BUDGET_FCU,
        },
        "disclaimer": (
            "Synthetic Northwind Mobile rules for the ChurnShield demo. "
            "Not a real operator policy and not evidence that the offer works."
        ),
    }
