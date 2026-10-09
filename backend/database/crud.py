"""Small, readable database helpers. Routes call these instead of writing SQL."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database.models import Customer, Prediction, Segment, User


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def create_user(db: Session, username: str, password_hash: str, role: str) -> User:
    user = User(username=username, password_hash=password_hash, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def upsert_customer(db: Session, values: dict) -> Customer:
    customer = db.get(Customer, values["customer_id"])
    if customer is None:
        customer = Customer(**values)
        db.add(customer)
    else:
        for key, value in values.items():
            setattr(customer, key, value)
    db.commit()
    return customer


def get_customer(db: Session, customer_id: str) -> Customer | None:
    return db.get(Customer, customer_id)


def list_customers(db: Session, search: str | None, limit: int = 100, offset: int = 0) -> list[Customer]:
    stmt = select(Customer)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(Customer.customer_id.like(like))
    stmt = stmt.order_by(Customer.customer_id).limit(limit).offset(offset)
    return list(db.scalars(stmt))


def upsert_prediction(
    db: Session,
    customer_id: str,
    churn_probability: float,
    predicted_churn: str,
    risk_level: str,
) -> Prediction:
    existing = db.scalar(select(Prediction).where(Prediction.customer_id == customer_id))
    if existing is None:
        existing = Prediction(
            customer_id=customer_id,
            churn_probability=churn_probability,
            predicted_churn=predicted_churn,
            risk_level=risk_level,
            prediction_date=datetime.utcnow(),
        )
        db.add(existing)
    else:
        existing.churn_probability = churn_probability
        existing.predicted_churn = predicted_churn
        existing.risk_level = risk_level
        existing.prediction_date = datetime.utcnow()
    db.commit()
    db.refresh(existing)
    return existing


def get_prediction(db: Session, customer_id: str) -> Prediction | None:
    return db.scalar(select(Prediction).where(Prediction.customer_id == customer_id))


def count_customers(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Customer)) or 0


def upsert_segment(db: Session, customer_id: str, cluster_id: int, segment_name: str) -> None:
    existing = db.get(Segment, customer_id)
    if existing is None:
        db.add(Segment(customer_id=customer_id, cluster_id=cluster_id, segment_name=segment_name))
    else:
        existing.cluster_id = cluster_id
        existing.segment_name = segment_name
    db.commit()
