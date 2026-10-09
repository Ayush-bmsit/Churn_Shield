from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_roles
from backend.database.connection import get_db
from backend.database.models import Customer, Prediction, Segment

router = APIRouter(tags=["analytics"])


@router.get("/analytics")
def analytics(db: Session = Depends(get_db), _user=Depends(require_roles("manager"))):
    total = db.scalar(select(func.count()).select_from(Customer)) or 0
    avg_p = db.scalar(select(func.avg(Prediction.churn_probability))) or 0.0

    risk_rows = db.execute(
        select(Prediction.risk_level, func.count()).group_by(Prediction.risk_level)
    ).all()
    risk_distribution = {level: count for level, count in risk_rows}

    contract_rows = db.execute(
        select(Customer.contract, func.count()).group_by(Customer.contract)
    ).all()
    contract_distribution = {name: count for name, count in contract_rows}

    churn_by_contract = []
    rows = db.execute(
        select(
            Customer.contract,
            func.avg(Prediction.churn_probability),
            func.avg(case((Prediction.predicted_churn == "Yes", 1), else_=0)),
            func.count(),
        )
        .join(Prediction, Prediction.customer_id == Customer.customer_id)
        .group_by(Customer.contract)
    ).all()
    for contract, avg_prob, pct_yes, n in rows:
        churn_by_contract.append(
            {
                "contract": contract,
                "avg_churn_probability": float(avg_prob or 0),
                "predicted_churn_rate": float(pct_yes or 0),
                "count": int(n),
            }
        )

    tenure_case = case(
        (Customer.tenure < 12, "0-11 months"),
        (Customer.tenure < 24, "12-23 months"),
        (Customer.tenure < 48, "24-47 months"),
        else_="48+ months",
    )
    tenure_rows = db.execute(
        select(
            tenure_case.label("tenure_group"),
            func.avg(Prediction.churn_probability),
            func.count(),
        )
        .join(Prediction, Prediction.customer_id == Customer.customer_id)
        .group_by(tenure_case)
    ).all()
    churn_by_tenure = [
        {
            "tenure_group": g,
            "avg_churn_probability": float(avg_prob or 0),
            "count": int(n),
        }
        for g, avg_prob, n in tenure_rows
    ]

    high_risk_high_charge = db.execute(
        select(
            Customer.customer_id,
            Customer.monthly_charges,
            Customer.tenure,
            Customer.contract,
            Prediction.churn_probability,
            Prediction.risk_level,
        )
        .join(Prediction, Prediction.customer_id == Customer.customer_id)
        .where(Prediction.risk_level == "High", Customer.monthly_charges >= 70)
        .order_by(Prediction.churn_probability.desc())
        .limit(25)
    ).mappings().all()

    return {
        "total_customers": int(total),
        "average_predicted_churn_probability": float(avg_p),
        "risk_distribution": {
            "High": int(risk_distribution.get("High", 0)),
            "Medium": int(risk_distribution.get("Medium", 0)),
            "Low": int(risk_distribution.get("Low", 0)),
        },
        "contract_distribution": contract_distribution,
        "predicted_churn_by_contract": churn_by_contract,
        "predicted_churn_by_tenure_group": churn_by_tenure,
        "high_risk_high_monthly_charges": [dict(r) for r in high_risk_high_charge],
        "notes": (
            "All figures are computed from MySQL predictions, not from hardcoded values. "
            "Risk buckets are project-defined (Low < 0.30, Medium 0.30-0.70, High > 0.70)."
        ),
    }


@router.get("/segments")
def segments(db: Session = Depends(get_db), _user=Depends(require_roles("manager"))):
    rows = db.execute(
        select(
            Segment.cluster_id,
            Segment.segment_name,
            func.count(),
            func.avg(Customer.tenure),
            func.avg(Customer.monthly_charges),
            func.avg(Prediction.churn_probability),
        )
        .join(Customer, Customer.customer_id == Segment.customer_id)
        .join(Prediction, Prediction.customer_id == Segment.customer_id, isouter=True)
        .group_by(Segment.cluster_id, Segment.segment_name)
        .order_by(Segment.cluster_id)
    ).all()
    return {
        "segments": [
            {
                "cluster_id": int(cid),
                "segment_name": name,
                "count": int(n),
                "avg_tenure": float(avg_t or 0),
                "avg_monthly_charges": float(avg_m or 0),
                "avg_churn_probability": float(avg_p or 0),
            }
            for cid, name, n, avg_t, avg_m, avg_p in rows
        ],
        "naming_note": (
            "Segment names come from K-Means cluster means for tenure and MonthlyCharges "
            "compared with overall medians. They are descriptive labels, not value scores."
        ),
    }
