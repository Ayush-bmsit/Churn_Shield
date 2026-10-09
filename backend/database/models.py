"""SQLAlchemy tables used by the application (not the training CSV)."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    gender: Mapped[str | None] = mapped_column(String(32), nullable=True)
    senior_citizen: Mapped[int | None] = mapped_column(Integer, nullable=True)
    partner: Mapped[str | None] = mapped_column(String(32), nullable=True)
    dependents: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tenure: Mapped[int | None] = mapped_column(Integer, nullable=True)
    phone_service: Mapped[str | None] = mapped_column(String(64), nullable=True)
    multiple_lines: Mapped[str | None] = mapped_column(String(64), nullable=True)
    internet_service: Mapped[str | None] = mapped_column(String(64), nullable=True)
    online_security: Mapped[str | None] = mapped_column(String(64), nullable=True)
    online_backup: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device_protection: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tech_support: Mapped[str | None] = mapped_column(String(64), nullable=True)
    streaming_tv: Mapped[str | None] = mapped_column(String(64), nullable=True)
    streaming_movies: Mapped[str | None] = mapped_column(String(64), nullable=True)
    contract: Mapped[str | None] = mapped_column(String(64), nullable=True)
    paperless_billing: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    monthly_charges: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_charges: Mapped[float | None] = mapped_column(Float, nullable=True)


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (UniqueConstraint("customer_id", name="uq_predictions_customer_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.customer_id"), nullable=False)
    churn_probability: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_churn: Mapped[str] = mapped_column(String(8), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    prediction_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Segment(Base):
    __tablename__ = "segments"

    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.customer_id"), primary_key=True)
    cluster_id: Mapped[int] = mapped_column(Integer, nullable=False)
    segment_name: Mapped[str] = mapped_column(String(128), nullable=False)
