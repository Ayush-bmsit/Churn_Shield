import pandas as pd
import streamlit as st

from frontend.api_client import ApiClient, ApiError


def render(api: ApiClient) -> None:
    st.title("Batch Prediction")
    st.write("Upload a CSV with the required feature columns. The backend scores every row with the saved pipeline.")

    try:
        template = api.batch_template()
    except ApiError as exc:
        template = "customerID,gender,SeniorCitizen,Partner,Dependents,tenure,PhoneService,MultipleLines,InternetService,OnlineSecurity,OnlineBackup,DeviceProtection,TechSupport,StreamingTV,StreamingMovies,Contract,PaperlessBilling,PaymentMethod,MonthlyCharges,TotalCharges\n"
        st.warning(f"Could not load template from API: {exc.detail}")

    st.download_button("Download CSV template", template, file_name="churn_batch_template.csv", mime="text/csv")

    uploaded = st.file_uploader("Upload customer CSV", type=["csv"])
    if uploaded and st.button("Run batch prediction"):
        try:
            result = api.batch_predict(uploaded.getvalue(), uploaded.name)
        except ApiError as exe:
            st.error(str(exe.detail))
            return
        st.success(f"Scored {result['row_count']} rows (saved {result['saved']}).")
        if result.get("unexpected_columns_ignored"):
            st.info(f"Ignored extra columns: {result['unexpected_columns_ignored']}")
        table = pd.DataFrame(result["results"]).rename(
            columns={
                "customerID": "customerID",
                "churn_probability": "churn_probability",
                "predicted_churn": "predicted_churn",
                "risk_level": "risk_level",
            }
        )
        st.dataframe(table, use_container_width=True)
        st.download_button(
            "Download prediction results",
            table.to_csv(index=False),
            file_name="churn_batch_results.csv",
            mime="text/csv",
        )
