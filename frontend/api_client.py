"""HTTP client used by Streamlit. All data access goes through FastAPI — never MySQL."""

import os
from typing import Any

import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")


class ApiError(Exception):
    def __init__(self, status_code: int, detail: Any):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"{status_code}: {detail}")


class ApiClient:
    def __init__(self, token: str | None = None):
        self.token = token

    def _headers(self) -> dict:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _handle(self, response: requests.Response) -> Any:
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise ApiError(response.status_code, detail)
        if response.headers.get("content-type", "").startswith("text/plain"):
            return response.text
        if not response.content:
            return None
        return response.json()

    def login(self, username: str, password: str) -> dict:
        response = requests.post(
            f"{BACKEND_URL}/login",
            json={"username": username, "password": password},
            timeout=30,
        )
        return self._handle(response)

    def predict(self, payload: dict) -> dict:
        response = requests.post(f"{BACKEND_URL}/predict", json=payload, headers=self._headers(), timeout=60)
        return self._handle(response)

    def batch_predict(self, file_bytes: bytes, filename: str) -> dict:
        response = requests.post(
            f"{BACKEND_URL}/batch-predict",
            files={"file": (filename, file_bytes, "text/csv")},
            headers=self._headers(),
            timeout=120,
        )
        return self._handle(response)

    def batch_template(self) -> str:
        response = requests.get(f"{BACKEND_URL}/batch-template", headers=self._headers(), timeout=30)
        return self._handle(response)

    def get_customer(self, customer_id: str) -> dict:
        response = requests.get(f"{BACKEND_URL}/customers/{customer_id}", headers=self._headers(), timeout=30)
        return self._handle(response)

    def list_customers(self, search: str | None = None, limit: int = 50) -> dict:
        params = {"limit": limit}
        if search:
            params["search"] = search
        response = requests.get(f"{BACKEND_URL}/customers", params=params, headers=self._headers(), timeout=30)
        return self._handle(response)

    def analytics(self) -> dict:
        response = requests.get(f"{BACKEND_URL}/analytics", headers=self._headers(), timeout=60)
        return self._handle(response)

    def segments(self) -> dict:
        response = requests.get(f"{BACKEND_URL}/segments", headers=self._headers(), timeout=60)
        return self._handle(response)

    def chat(self, question: str) -> dict:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={"question": question},
            headers=self._headers(),
            timeout=90,
        )
        return self._handle(response)
