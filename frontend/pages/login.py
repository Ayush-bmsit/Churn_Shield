import streamlit as st

from frontend.api_client import ApiClient, ApiError


def render() -> None:
    st.title("Telco Churn Prototype")
    st.write("Sign in to use prediction, analytics, and the AI assistant.")
    st.info("DEMO accounts (local development only): `manager` / `manager123` and `employee` / `employee123`.")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        try:
            data = ApiClient().login(username, password)
        except ApiError as exc:
            st.error(f"Login failed: {exc.detail}")
            return
        st.session_state.token = data["access_token"]
        st.session_state.role = data["role"]
        st.session_state.username = data["username"]
        st.rerun()
