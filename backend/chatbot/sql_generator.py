"""Generate SQL with the LLM, validate it is read-only, run it as chatbot_user."""

import re

from sqlalchemy import text

from backend.chatbot import service as llm
from backend.chatbot.prompts import ANSWER_SYSTEM_PROMPT, SQL_SYSTEM_PROMPT
from backend.database.connection import chatbot_engine

FORBIDDEN = [
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
    "replace",
    "grant",
    "revoke",
    "load",
    "outfile",
    "dumpfile",
    "into outfile",
    "lock ",
    "unlock ",
    "call ",
    "exec",
    "execute",
    "prepare",
    "handler",
    "shutdown",
]


def extract_sql(raw: str) -> str:
    text_sql = raw.strip()
    fence = re.search(r"```(?:sql)?\s*(.*?)```", text_sql, flags=re.IGNORECASE | re.DOTALL)
    if fence:
        text_sql = fence.group(1).strip()
    text_sql = text_sql.strip().rstrip(";")
    return text_sql


def strip_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--.*?$", " ", sql, flags=re.MULTILINE)
    sql = re.sub(r"#.*?$", " ", sql, flags=re.MULTILINE)
    return sql.strip()


def validate_select_only(sql: str) -> str:
    cleaned = strip_comments(sql)
    if not cleaned:
        raise ValueError("Empty SQL")
    if ";" in cleaned:
        raise ValueError("Multiple SQL statements are not allowed")
    lowered = " " + re.sub(r"\s+", " ", cleaned.lower()) + " "
    for word in FORBIDDEN:
        if word in lowered:
            raise ValueError(f"Rejected SQL: contains forbidden keyword '{word.strip()}'")
    first = cleaned.lstrip().split(None, 1)[0].lower()
    if first not in {"select", "with"}:
        raise ValueError("Only SELECT / WITH queries are allowed")
    return cleaned


def run_readonly_sql(sql: str) -> list[dict]:
    validated = validate_select_only(sql)
    with chatbot_engine.connect() as conn:
        result = conn.execute(text(validated))
        rows = result.mappings().all()
    return [dict(row) for row in rows[:100]]


def answer_question(question: str) -> dict:
    sql_raw = llm.complete(SQL_SYSTEM_PROMPT, question)
    sql = extract_sql(sql_raw)
    try:
        validated = validate_select_only(sql)
    except ValueError as exc:
        return {
            "ok": False,
            "error": str(exc),
            "sql": sql,
            "answer": None,
            "rows": [],
        }
    try:
        rows = run_readonly_sql(validated)
    except Exception as exc:
        return {
            "ok": False,
            "error": f"SQL failed (MySQL or validator): {exc}",
            "sql": validated,
            "answer": None,
            "rows": [],
        }

    preview = rows[:20]
    user_msg = f"Question: {question}\nSQL: {validated}\nRows: {preview}\nRow count returned: {len(rows)}"
    answer = llm.complete(ANSWER_SYSTEM_PROMPT, user_msg)
    return {
        "ok": True,
        "error": None,
        "sql": validated,
        "answer": answer,
        "rows": preview,
    }
