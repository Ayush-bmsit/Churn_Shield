import pandas as pd
import streamlit as st

from frontend.api_client import ApiClient, ApiError


def render(api: ApiClient) -> None:
    st.title("ChurnShield — Analytics")
    st.write("Aggregates computed from MySQL customer and prediction tables.")

    try:
        data = api.analytics()
        segments = api.segments()
    except ApiError as exc:
        st.error(str(exc.detail))
        return

    risk = data["risk_distribution"]
    a, b, c, d = st.columns(4)
    a.metric("Total customers", data["total_customers"])
    b.metric("High risk", risk.get("High", 0))
    c.metric("Medium risk", risk.get("Medium", 0))
    d.metric("Low risk", risk.get("Low", 0))
    st.metric("Average predicted churn probability", f"{data['average_predicted_churn_probability']:.3f}")
    st.caption(data.get("notes", ""))

    st.subheader("Risk distribution")
    st.bar_chart(pd.DataFrame({"customers": risk}))

    st.subheader("Contract distribution")
    st.bar_chart(pd.DataFrame({"customers": data.get("contract_distribution") or {}}))

    st.subheader("Predicted churn by contract type")
    st.dataframe(pd.DataFrame(data.get("predicted_churn_by_contract") or []), use_container_width=True)

    st.subheader("Predicted churn by tenure group")
    tenure_df = pd.DataFrame(data.get("predicted_churn_by_tenure_group") or [])
    if not tenure_df.empty:
        st.bar_chart(tenure_df.set_index("tenure_group")[["avg_churn_probability"]])
        st.dataframe(tenure_df, use_container_width=True)

    st.subheader("High-risk + high monthly charges")
    st.dataframe(pd.DataFrame(data.get("high_risk_high_monthly_charges") or []), use_container_width=True)

    st.subheader("Segments")
    st.caption(segments.get("naming_note", ""))
    st.dataframe(pd.DataFrame(segments.get("segments") or []), use_container_width=True)
