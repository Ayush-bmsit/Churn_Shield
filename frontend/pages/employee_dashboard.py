import streamlit as st

from frontend.api_client import ApiClient, ApiError


def render(api: ApiClient) -> None:
    st.title("Employee dashboard")
    st.write(
        "Use this page to look up a customer, then open Customer Prediction for a new score "
        "or Batch Prediction for a CSV."
    )

    customer_id = st.text_input("Customer ID lookup")
    if st.button("Search") and customer_id.strip():
        try:
            data = api.get_customer(customer_id.strip())
        except ApiError as exc:
            st.error(str(exc.detail))
            return
        st.subheader(data.get("customerID"))
        pred = data.get("prediction") or {}
        cols = st.columns(3)
        cols[0].metric("Probability", f"{pred.get('churn_probability', 'n/a')}")
        cols[1].metric("Predicted churn", pred.get("predicted_churn", "n/a"))
        cols[2].metric("Risk", pred.get("risk_level", "n/a"))
        st.json(
            {
                "Contract": data.get("Contract"),
                "tenure": data.get("tenure"),
                "MonthlyCharges": data.get("MonthlyCharges"),
                "InternetService": data.get("InternetService"),
                "PaymentMethod": data.get("PaymentMethod"),
            }
        )
