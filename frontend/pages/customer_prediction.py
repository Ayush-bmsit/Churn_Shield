import streamlit as st

from frontend.api_client import ApiClient, ApiError
from frontend.components.ui import show_explanation, show_recommendations, show_risk

CONTRACTS = ["Month-to-month", "One year", "Two year"]
YES_NO = ["Yes", "No"]
INTERNET = ["DSL", "Fiber optic", "No"]
PHONE_MULTI = ["No phone service", "No", "Yes"]
INTERNET_ADDON = ["No internet service", "No", "Yes"]
PAYMENTS = [
    "Electronic check",
    "Mailed check",
    "Bank transfer (automatic)",
    "Credit card (automatic)",
]


def render(api: ApiClient) -> None:
    st.title("ChurnShield — Customer prediction")
    st.write("Scores one customer with the saved pipeline, then applies the synthetic retention rules.")

    lookup = st.text_input("Optional: load an existing customer ID")
    prefill = {}
    if st.button("Load customer") and lookup.strip():
        try:
            prefill = api.get_customer(lookup.strip())
            st.session_state["prefill"] = prefill
        except ApiError as exc:
            st.error(str(exc.detail))
    prefill = st.session_state.get("prefill") or {}

    with st.form("predict_form"):
        customer_id = st.text_input("customerID", value=prefill.get("customerID", "demo-001"))
        c1, c2, c3 = st.columns(3)
        gender = c1.selectbox("gender", ["Female", "Male"], index=0 if prefill.get("gender") != "Male" else 1)
        senior = c2.selectbox("SeniorCitizen", [0, 1], index=int(prefill.get("SeniorCitizen") or 0))
        partner = c3.selectbox("Partner", YES_NO, index=_idx(YES_NO, prefill.get("Partner")))
        dependents = c1.selectbox("Dependents", YES_NO, index=_idx(YES_NO, prefill.get("Dependents")))
        tenure = c2.number_input("tenure", min_value=0, max_value=100, value=int(prefill.get("tenure") or 1))
        phone = c3.selectbox("PhoneService", YES_NO, index=_idx(YES_NO, prefill.get("PhoneService"), default="Yes"))
        multiple = c1.selectbox("MultipleLines", PHONE_MULTI, index=_idx(PHONE_MULTI, prefill.get("MultipleLines")))
        internet = c2.selectbox("InternetService", INTERNET, index=_idx(INTERNET, prefill.get("InternetService")))
        security = c3.selectbox("OnlineSecurity", INTERNET_ADDON, index=_idx(INTERNET_ADDON, prefill.get("OnlineSecurity")))
        backup = c1.selectbox("OnlineBackup", INTERNET_ADDON, index=_idx(INTERNET_ADDON, prefill.get("OnlineBackup")))
        protect = c2.selectbox("DeviceProtection", INTERNET_ADDON, index=_idx(INTERNET_ADDON, prefill.get("DeviceProtection")))
        tech = c3.selectbox("TechSupport", INTERNET_ADDON, index=_idx(INTERNET_ADDON, prefill.get("TechSupport")))
        tv = c1.selectbox("StreamingTV", INTERNET_ADDON, index=_idx(INTERNET_ADDON, prefill.get("StreamingTV")))
        movies = c2.selectbox("StreamingMovies", INTERNET_ADDON, index=_idx(INTERNET_ADDON, prefill.get("StreamingMovies")))
        contract = c3.selectbox("Contract", CONTRACTS, index=_idx(CONTRACTS, prefill.get("Contract")))
        paperless = c1.selectbox("PaperlessBilling", YES_NO, index=_idx(YES_NO, prefill.get("PaperlessBilling"), default="Yes"))
        pay = c2.selectbox("PaymentMethod", PAYMENTS, index=_idx(PAYMENTS, prefill.get("PaymentMethod")))
        monthly = c3.number_input(
            "MonthlyCharges", min_value=0.0, value=float(prefill.get("MonthlyCharges") or 70.0)
        )
        total = c1.number_input(
            "TotalCharges", min_value=0.0, value=float(prefill.get("TotalCharges") or 70.0)
        )
        submitted = st.form_submit_button("Predict")

    if submitted:
        payload = {
            "customerID": customer_id,
            "gender": gender,
            "SeniorCitizen": int(senior),
            "Partner": partner,
            "Dependents": dependents,
            "tenure": int(tenure),
            "PhoneService": phone,
            "MultipleLines": multiple,
            "InternetService": internet,
            "OnlineSecurity": security,
            "OnlineBackup": backup,
            "DeviceProtection": protect,
            "TechSupport": tech,
            "StreamingTV": tv,
            "StreamingMovies": movies,
            "Contract": contract,
            "PaperlessBilling": paperless,
            "PaymentMethod": pay,
            "MonthlyCharges": float(monthly),
            "TotalCharges": float(total),
            "save": True,
        }
        try:
            result = api.predict(payload)
        except ApiError as exc:
            st.error(str(exc.detail))
            return
        show_risk(
            result["churn_probability"],
            result["risk_level"],
            predicted=result.get("predicted_churn"),
            threshold=result.get("decision_threshold"),
        )
        show_explanation(result.get("explanation") or {})
        show_recommendations(
            result.get("recommendations") or [],
            result.get("recommendations_note"),
            result.get("decision_support"),
        )


def _idx(options: list[str], value, default=None) -> int:
    if value in options:
        return options.index(value)
    if default in options:
        return options.index(default)
    return 0
