"""Simple display helpers shared by pages."""

import streamlit as st


def show_risk(probability: float, risk: str, predicted: str | None = None, threshold: float | None = None) -> None:
    st.metric("Churn probability", f"{probability:.2f}")
    if predicted is None:
        cutoff = 0.5 if threshold is None else threshold
        predicted = "Yes" if probability >= cutoff else "No"
    st.metric("Predicted class", predicted)
    st.metric("Risk category", risk)
    cutoff_text = f"{threshold:.2f}" if threshold is not None else "the saved decision threshold"
    st.caption(
        f"Predicted class uses {cutoff_text}. "
        "Risk buckets are separate and project-defined: Low < 0.30, Medium 0.30–0.70, High > 0.70."
    )


def show_explanation(explanation: dict) -> None:
    st.subheader("Main factors contributing to this prediction")
    if not explanation or not explanation.get("ok"):
        st.warning(explanation.get("error") if explanation else "No explanation available.")
        return
    st.caption(f"Method: {explanation.get('method')} ({explanation.get('model_type')})")
    for factor in explanation.get("factors", []):
        st.write(f"- **{factor['label']}** ({factor['effect']}; SHAP={factor['shap_value']})")


def show_recommendations(items: list[str], note: str | None = None, decision: dict | None = None) -> None:
    st.subheader("Retention decision support")
    if note:
        st.caption(note)
    if decision:
        offer = decision.get("offer") or {}
        st.write(
            f"Outreach flag: **{'yes' if decision.get('flagged_for_outreach') else 'no'}**. "
            f"Offer eligible: **{'yes' if offer.get('eligible') else 'no'}**. "
            f"Approval: **{offer.get('approval', 'not_offered')}**."
        )
        if offer.get("tier"):
            st.write(
                f"Tier {offer['tier']}: {offer['discount_percent']}% for "
                f"{offer['duration_months']} months "
                f"({offer['monthly_discount_fcu']:.2f} FCU per month)."
            )
        sources = decision.get("policy_sources") or []
        if sources:
            st.caption(
                "Policy sources: "
                + "; ".join(f"{item['document']} — {item['section']}" for item in sources)
            )
        if decision.get("disclaimer"):
            st.caption(decision["disclaimer"])
    for item in items:
        st.write(f"- {item}")
