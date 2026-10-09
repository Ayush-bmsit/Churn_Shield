import pandas as pd
import streamlit as st

from frontend.api_client import ApiClient, ApiError


def render(api: ApiClient) -> None:
    st.title("AI Assistant")
    st.write(
        "Questions go Streamlit → FastAPI `/chat` → LLM (SQL) → read-only MySQL → LLM (answer). "
        "The chatbot does not run the churn model."
    )
    st.caption("Requires LLM_API_KEY on the backend. There are no placeholder answers.")

    if "chat_log" not in st.session_state:
        st.session_state.chat_log = []

    for item in st.session_state.chat_log:
        with st.chat_message("user"):
            st.write(item["question"])
        with st.chat_message("assistant"):
            if item.get("ok"):
                st.write(item.get("answer"))
                with st.expander("SQL used"):
                    st.code(item.get("sql") or "", language="sql")
                if item.get("rows"):
                    st.dataframe(pd.DataFrame(item["rows"]), use_container_width=True)
            else:
                st.error(item.get("error") or item.get("answer") or "Request failed")

    question = st.chat_input("Ask about stored customers, predictions, or segments")
    if question:
        try:
            result = api.chat(question)
            result["question"] = question
            st.session_state.chat_log.append(result)
        except ApiError as exc:
            st.session_state.chat_log.append(
                {"question": question, "ok": False, "error": str(exc.detail), "sql": None, "rows": []}
            )
        st.rerun()
