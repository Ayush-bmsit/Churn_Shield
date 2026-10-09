"""Create tables, demo users, optional customer load, predictions, and K-Means.

Demo credentials (LOCAL DEVELOPMENT ONLY):
  manager / manager123
  employee / employee123
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.auth.auth import hash_password  # noqa: E402
from backend.config import settings  # noqa: E402
from backend.database.connection import SessionLocal, engine, wait_for_db  # noqa: E402
from backend.database.models import Base, Customer, Prediction, Segment  # noqa: E402
from backend.database import crud  # noqa: E402
from backend.ml.predict import load_pipeline, pipeline_path, predict_frame  # noqa: E402
from backend.ml.preprocessing import ID_COL, model_dict_to_customer_values  # noqa: E402
from backend.ml.segmentation import fit_and_label  # noqa: E402
from backend.ml.train import train  # noqa: E402

DEMO_USERS = [
    ("manager", "manager123", "manager"),
    ("employee", "employee123", "employee"),
]


def tighten_chatbot_grants() -> None:
    """Replace database-wide SELECT with table-level SELECT. Never grant users."""
    root_url = (
        f"mysql+pymysql://root:{settings.mysql_root_password}"
        f"@{'mysql' if 'mysql:3306' in settings.database_url else 'localhost'}:3306/"
        f"{settings.mysql_database}"
    )
    from sqlalchemy import create_engine

    try:
        root_engine = create_engine(root_url, pool_pre_ping=True)
        dbname = settings.mysql_database
        user = settings.chatbot_db_user
        password = settings.chatbot_db_password
        with root_engine.begin() as conn:
            conn.execute(text(f"CREATE USER IF NOT EXISTS '{user}'@'%' IDENTIFIED BY :pw"), {"pw": password})
            conn.execute(text(f"ALTER USER '{user}'@'%' IDENTIFIED BY :pw"), {"pw": password})
            conn.execute(text(f"REVOKE ALL PRIVILEGES, GRANT OPTION FROM '{user}'@'%'"))
            conn.execute(text(f"GRANT SELECT ON {dbname}.customers TO '{user}'@'%'"))
            conn.execute(text(f"GRANT SELECT ON {dbname}.predictions TO '{user}'@'%'"))
            conn.execute(text(f"GRANT SELECT ON {dbname}.segments TO '{user}'@'%'"))
            conn.execute(text("FLUSH PRIVILEGES"))
        print("Chatbot user grants tightened to SELECT on customers, predictions, segments.")
    except Exception as exc:
        print(
            "Could not tighten chatbot grants automatically "
            f"(need root access from this process): {exc}. "
            "Grant SELECT on customers/predictions/segments manually if needed."
        )


def seed_users(db) -> None:
    for username, password, role in DEMO_USERS:
        if crud.get_user_by_username(db, username) is None:
            crud.create_user(db, username, hash_password(password), role)
            print(f"Created DEMO user {username} / {password} (role={role})")
        else:
            print(f"User {username} already exists")


def ensure_model() -> None:
    if not pipeline_path().exists():
        print("No saved pipeline found. Training now (offline script, not an HTTP endpoint)...")
        train(csv_path=settings.csv_path, models_dir=settings.models_dir)
    load_pipeline()


def load_customers_and_score(db) -> None:
    existing = crud.count_customers(db)
    if existing > 0:
        print(f"Customers already loaded ({existing}). Skipping CSV import.")
        return
    csv_path = Path(settings.csv_path)
    if not csv_path.exists():
        print(f"CSV not found at {csv_path}; skipping customer import.")
        return
    df = pd.read_csv(csv_path)
    scored = predict_frame(df)
    print(f"Importing {len(scored)} customers + predictions...")
    customers = []
    predictions = []
    for row in scored.to_dict(orient="records"):
        values = model_dict_to_customer_values(row)
        customers.append(Customer(**values))
        predictions.append(
            Prediction(
                customer_id=values["customer_id"],
                churn_probability=float(row["churn_probability"]),
                predicted_churn=str(row["predicted_churn"]),
                risk_level=str(row["risk_level"]),
            )
        )
    db.add_all(customers)
    db.commit()
    db.add_all(predictions)
    db.commit()
    print("Customer import complete.")

    labeled, _meta = fit_and_label(scored)
    segments = []
    for row in labeled.to_dict(orient="records"):
        cid = str(row.get(ID_COL) or row.get("customerID"))
        segments.append(
            Segment(
                customer_id=cid,
                cluster_id=int(row["cluster_id"]),
                segment_name=str(row["segment_name"]),
            )
        )
    db.add_all(segments)
    db.commit()
    print("K-Means segments stored.")


def main() -> None:
    wait_for_db()
    Base.metadata.create_all(bind=engine)
    tighten_chatbot_grants()
    db = SessionLocal()
    try:
        seed_users(db)
        if settings.seed_on_startup:
            ensure_model()
            load_customers_and_score(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
