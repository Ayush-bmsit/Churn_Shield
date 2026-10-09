"""SQLAlchemy engines. The app engine uses the application DB user.
The chatbot engine uses a separate SELECT-only user when executing LLM SQL."""

from collections.abc import Generator
import time

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from backend.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

chatbot_engine = create_engine(settings.chatbot_database_url, pool_pre_ping=True)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def wait_for_db(retries: int = 40, delay_seconds: float = 2.0) -> None:
    last_error = None
    for _ in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception as exc:
            last_error = exc
            time.sleep(delay_seconds)
    raise RuntimeError(f"Could not connect to MySQL: {last_error}")
