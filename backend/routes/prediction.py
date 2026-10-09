from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import pandas as pd
import io

from backend.auth.dependencies import require_roles
from backend.database.connection import get_db
from backend.database import crud
from backend.ml.decision_support import build_decision
from backend.ml.explain import explain_one
from backend.ml.predict import predict_frame, predict_one, template_columns
from backend.ml.preprocessing import FEATURE_COLUMNS, ID_COL, model_dict_to_customer_values

router = APIRouter(tags=["prediction"])


class PredictRequest(BaseModel):
    customerID: str = "adhoc-customer"
    gender: str = "Female"
    SeniorCitizen: int = Field(0, ge=0, le=1)
    Partner: str = "No"
    Dependents: str = "No"
    tenure: int = Field(1, ge=0)
    PhoneService: str = "Yes"
    MultipleLines: str = "No"
    InternetService: str = "Fiber optic"
    OnlineSecurity: str = "No"
    OnlineBackup: str = "No"
    DeviceProtection: str = "No"
    TechSupport: str = "No"
    StreamingTV: str = "No"
    StreamingMovies: str = "No"
    Contract: str = "Month-to-month"
    PaperlessBilling: str = "Yes"
    PaymentMethod: str = "Electronic check"
    MonthlyCharges: float = 70.0
    TotalCharges: float = 70.0
    save: bool = True


def _full_response(features: dict, save: bool, db: Session) -> dict:
    prediction = predict_one(features)
    explanation = explain_one(features)
    decision = build_decision(
        features,
        prediction["churn_probability"],
        decision_threshold=prediction["decision_threshold"],
        explanation_ok=bool(explanation.get("ok")),
    )
    suggestions = decision["messages"]
    if save:
        crud.upsert_customer(db, model_dict_to_customer_values(features))
        crud.upsert_prediction(
            db,
            str(features.get(ID_COL) or features.get("customerID")),
            prediction["churn_probability"],
            prediction["predicted_churn"],
            prediction["risk_level"],
        )
    return {
        **prediction,
        "risk_thresholds_note": (
            "Risk buckets are project-defined: Low < 0.30, Medium 0.30-0.70, High > 0.70. "
            "They are not universal statistical or medical thresholds."
        ),
        "explanation": explanation,
        "recommendations": suggestions,
        "decision_support": decision,
        "recommendations_note": (
            "Suggestions apply the synthetic Northwind Mobile policy rules to the model score. "
            "They are not learned by the model and they do not prove that an offer prevents churn."
        ),
    }


@router.post("/predict")
def predict(
    body: PredictRequest,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("manager", "employee")),
):
    features = body.model_dump()
    features.pop("save", None)
    try:
        return _full_response(features, save=body.save, db=db)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/batch-template", response_class=PlainTextResponse)
def batch_template(_user=Depends(require_roles("manager", "employee"))):
    return ",".join(template_columns()) + "\n"


@router.post("/batch-predict")
async def batch_predict(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("manager", "employee")),
):
    raw = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read CSV: {exc}") from exc

    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    unexpected = [c for c in df.columns if c not in template_columns() and c != "Churn"]
    if missing:
        raise HTTPException(
            status_code=400,
            detail={"missing_columns": missing, "unexpected_columns": unexpected},
        )
    if ID_COL not in df.columns:
        df[ID_COL] = [f"row-{i}" for i in range(len(df))]

    try:
        scored = predict_frame(df)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    saved = 0
    for _, row in scored.iterrows():
        values = model_dict_to_customer_values(row.to_dict())
        crud.upsert_customer(db, values)
        crud.upsert_prediction(
            db,
            values["customer_id"],
            float(row["churn_probability"]),
            str(row["predicted_churn"]),
            str(row["risk_level"]),
        )
        saved += 1

    records = scored[[ID_COL, "churn_probability", "predicted_churn", "risk_level"]].to_dict(orient="records")
    return {
        "row_count": len(records),
        "saved": saved,
        "unexpected_columns_ignored": unexpected,
        "missing_columns": [],
        "results": records,
    }
