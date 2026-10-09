"""Shared cleaning and feature lists for training and inference.

The sklearn Pipeline saved during training applies encoding/scaling.
This file only handles CSV typing/missing values so both train and predict
start from the same raw column names.
"""

import pandas as pd

ID_COL = "customerID"
TARGET_COL = "Churn"

NUMERIC_FEATURES = ["tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen"]
CATEGORICAL_FEATURES = [
    "gender",
    "Partner",
    "Dependents",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
]
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TEMPLATE_COLUMNS = [ID_COL] + FEATURE_COLUMNS

# Project-defined business thresholds (not universal statistical cutoffs).
LOW_RISK_MAX = 0.30
HIGH_RISK_MIN = 0.70


def risk_level(probability: float) -> str:
    if probability < LOW_RISK_MAX:
        return "Low"
    if probability <= HIGH_RISK_MIN:
        return "Medium"
    return "High"


def predicted_label(probability: float, threshold: float = 0.5) -> str:
    return "Yes" if probability >= threshold else "No"


def clean_features(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce types used by the model. Does not one-hot encode (the pipeline does).

    Blank TotalCharges are set to 0 only when tenure is 0. On this dataset those
    blanks are new accounts with no accumulated bill. Any other missing numeric
    value is left for the median imputer inside the training pipeline.
    """
    out = df.copy()
    if "tenure" in out.columns:
        out["tenure"] = pd.to_numeric(out["tenure"], errors="coerce")
    if "TotalCharges" in out.columns:
        charges = pd.to_numeric(out["TotalCharges"], errors="coerce")
        if "tenure" in out.columns:
            new_account = charges.isna() & out["tenure"].eq(0)
            charges = charges.mask(new_account, 0)
        out["TotalCharges"] = charges
    if "MonthlyCharges" in out.columns:
        out["MonthlyCharges"] = pd.to_numeric(out["MonthlyCharges"], errors="coerce")
    if "SeniorCitizen" in out.columns:
        out["SeniorCitizen"] = pd.to_numeric(out["SeniorCitizen"], errors="coerce")
    return out


def customer_row_to_model_dict(customer) -> dict:
    """Map a SQLAlchemy Customer to the CSV-style column names the pipeline expects."""
    return {
        ID_COL: customer.customer_id,
        "gender": customer.gender,
        "SeniorCitizen": customer.senior_citizen,
        "Partner": customer.partner,
        "Dependents": customer.dependents,
        "tenure": customer.tenure,
        "PhoneService": customer.phone_service,
        "MultipleLines": customer.multiple_lines,
        "InternetService": customer.internet_service,
        "OnlineSecurity": customer.online_security,
        "OnlineBackup": customer.online_backup,
        "DeviceProtection": customer.device_protection,
        "TechSupport": customer.tech_support,
        "StreamingTV": customer.streaming_tv,
        "StreamingMovies": customer.streaming_movies,
        "Contract": customer.contract,
        "PaperlessBilling": customer.paperless_billing,
        "PaymentMethod": customer.payment_method,
        "MonthlyCharges": customer.monthly_charges,
        "TotalCharges": customer.total_charges,
    }


def model_dict_to_customer_values(row: dict) -> dict:
    return {
        "customer_id": str(row[ID_COL]),
        "gender": row.get("gender"),
        "senior_citizen": int(row.get("SeniorCitizen") or 0),
        "partner": row.get("Partner"),
        "dependents": row.get("Dependents"),
        "tenure": int(row.get("tenure") or 0),
        "phone_service": row.get("PhoneService"),
        "multiple_lines": row.get("MultipleLines"),
        "internet_service": row.get("InternetService"),
        "online_security": row.get("OnlineSecurity"),
        "online_backup": row.get("OnlineBackup"),
        "device_protection": row.get("DeviceProtection"),
        "tech_support": row.get("TechSupport"),
        "streaming_tv": row.get("StreamingTV"),
        "streaming_movies": row.get("StreamingMovies"),
        "contract": row.get("Contract"),
        "paperless_billing": row.get("PaperlessBilling"),
        "payment_method": row.get("PaymentMethod"),
        "monthly_charges": float(row.get("MonthlyCharges") or 0),
        "total_charges": float(row.get("TotalCharges") or 0),
    }
