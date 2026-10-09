from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_roles
from backend.database.connection import get_db
from backend.database import crud
from backend.database.models import Customer, Prediction, Segment
from backend.ml.preprocessing import customer_row_to_model_dict

router = APIRouter(tags=["customers"])


def _serialize_customer(db: Session, customer: Customer) -> dict:
    pred = crud.get_prediction(db, customer.customer_id)
    segment = db.get(Segment, customer.customer_id)
    payload = customer_row_to_model_dict(customer)
    payload["prediction"] = None
    payload["segment"] = None
    if pred:
        payload["prediction"] = {
            "churn_probability": pred.churn_probability,
            "predicted_churn": pred.predicted_churn,
            "risk_level": pred.risk_level,
            "prediction_date": pred.prediction_date.isoformat() if pred.prediction_date else None,
        }
    if segment:
        payload["segment"] = {
            "cluster_id": segment.cluster_id,
            "segment_name": segment.segment_name,
        }
    return payload


@router.get("/customers")
def list_customers(
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user=Depends(require_roles("manager", "employee")),
):
    if user.role == "employee" and not search:
        raise HTTPException(
            status_code=403,
            detail="Employees must look up a specific customer_id (use search).",
        )
    rows = crud.list_customers(db, search=search, limit=limit, offset=offset)
    return {"count": len(rows), "customers": [_serialize_customer(db, c) for c in rows]}


@router.get("/customers/{customer_id}")
def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("manager", "employee")),
):
    customer = crud.get_customer(db, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return _serialize_customer(db, customer)
