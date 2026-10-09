import pandas as pd
import streamlit as st

from frontend.api_client import ApiClient, ApiError


def render(api: ApiClient) -> None:
    st.title("Manager dashboard")
    st.write("Overview of stored customers and model scores. Open Analytics for the full breakdown.")

    try:
        analytics = api.analytics()
        segments = api.segments()
    except ApiError as exc:
        st.error(str(exc.detail))
        return

    risk = analytics["risk_distribution"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total customers", analytics["total_customers"])
    c2.metric("High risk", risk.get("High", 0))
    c3.metric("Medium risk", risk.get("Medium", 0))
    c4.metric("Low risk", risk.get("Low", 0))
    st.metric("Average predicted churn probability", f"{analytics['average_predicted_churn_probability']:.3f}")
    st.caption(analytics.get("notes", ""))

    st.subheader("Risk distribution")
    st.bar_chart(pd.DataFrame({"count": risk}))

    st.subheader("Customer segments (K-Means)")
    st.caption(segments.get("naming_note", ""))
    if segments.get("segments"):
        st.dataframe(pd.DataFrame(segments["segments"]), use_container_width=True)

    st.subheader("High-risk customers with monthly charges ≥ 70")
    rows = analytics.get("high_risk_high_monthly_charges") or []
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.write("None in the current database.")
