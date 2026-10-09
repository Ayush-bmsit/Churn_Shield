"""Streamlit UI. Role-based navigation; talks only to FastAPI."""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.api_client import ApiClient  # noqa: E402
from frontend.pages import (  # noqa: E402
    analytics,
    batch_prediction,
    chatbot,
    customer_prediction,
    employee_dashboard,
    login,
    manager_dashboard,
)

st.set_page_config(page_title="ChurnShield", layout="wide")

EMPLOYEE_PAGES = {
    "Employee dashboard": employee_dashboard,
    "Customer Prediction": customer_prediction,
    "Batch Prediction": batch_prediction,
    "AI Assistant": chatbot,
}
MANAGER_PAGES = {
    "Manager dashboard": manager_dashboard,
    "Analytics": analytics,
    "Customer Prediction": customer_prediction,
    "Batch Prediction": batch_prediction,
    "AI Assistant": chatbot,
}


def main() -> None:
    if not st.session_state.get("token"):
        login.render()
        return

    role = st.session_state.get("role")
    pages = MANAGER_PAGES if role == "manager" else EMPLOYEE_PAGES
    with st.sidebar:
        st.header("ChurnShield")
        st.caption("Customer retention decision support")
        st.write(f"Signed in as **{st.session_state.get('username')}** ({role})")
        choice = st.radio("Go to", list(pages.keys()))
        if st.button("Log out"):
            for key in ("token", "role", "username", "prefill", "chat_log"):
                st.session_state.pop(key, None)
            st.rerun()

    api = ApiClient(token=st.session_state["token"])
    pages[choice].render(api)


if __name__ == "__main__":
    main()
