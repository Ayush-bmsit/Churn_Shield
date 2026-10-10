"""Load configuration from environment variables. Never hardcode secrets here."""

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT_DIR / ".env"), extra="ignore")

    database_url: str = "mysql+pymysql://churn_app:change_this_app_password@localhost:3306/churn_db"
    chatbot_database_url: str = (
        "mysql+pymysql://chatbot_user:change_this_chatbot_password@localhost:3306/churn_db"
    )
    mysql_root_password: str = "change_this_root_password"
    chatbot_db_user: str = "chatbot_user"
    chatbot_db_password: str = "change_this_chatbot_password"
    mysql_database: str = "churn_db"

    jwt_secret: str = "change_this_to_a_long_random_string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    seed_on_startup: bool = True
    csv_path: str = str(ROOT_DIR / "data" / "WA_Fn-UseC_-Telco-Customer-Churn.csv")
    models_dir: str = str(ROOT_DIR / "models")

    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = ""
    llm_timeout_seconds: int = 60

    @field_validator("csv_path", "models_dir")
    @classmethod
    def _anchor_to_project(cls, value: str) -> str:
        path = Path(value)
        if not path.is_absolute():
            path = ROOT_DIR / path
        return str(path.resolve())


settings = Settings()
