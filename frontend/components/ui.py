"""Simple display helpers shared by pages."""

import streamlit as st


def show_risk(probability: float, risk: str) -> None:
    st.metric("Churn probability", f"{probability:.2f}")
    st.metric("Predicted class", "Yes" if probability >= 0.5 else "No")
    st.metric("Risk", risk)
    st.caption(
        "Risk buckets are project-defined: Low < 0.30, Medium 0.30–0.70, High > 0.70. "
        "They are not universal statistical thresholds."
    )


def show_explanation(explanation: dict) -> None:
    st.subheader("Main factors contributing to this prediction")
    if not explanation or not explanation.get("ok"):
        st.warning(explanation.get("error") if explanation else "No explanation available.")
        return
    st.caption(f"Method: {explanation.get('method')} ({explanation.get('model_type')})")
    for factor in explanation.get("factors", []):
        st.write(f"- **{factor['label']}** ({factor['effect']}; SHAP={factor['shap_value']})")


def show_recommendations(items: list[str], note: str | None = None) -> None:
    st.subheader("Suggested action (rule-based)")
    if note:
        st.caption(note)
    for item in items:
        st.write(f"- {item}")
