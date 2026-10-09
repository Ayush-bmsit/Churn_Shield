"""Prompts for SQL generation and natural-language answers.

The LLM is only given the analytics tables. The users table is intentionally omitted.
"""

SCHEMA_FOR_LLM = """
Tables available (MySQL). You may ONLY query these:

1) customers
   customer_id VARCHAR PRIMARY KEY
   gender VARCHAR
   senior_citizen INT  -- 0 or 1
   partner VARCHAR  -- Yes/No
   dependents VARCHAR
   tenure INT  -- months
   phone_service VARCHAR
   multiple_lines VARCHAR
   internet_service VARCHAR
   online_security VARCHAR
   online_backup VARCHAR
   device_protection VARCHAR
   tech_support VARCHAR
   streaming_tv VARCHAR
   streaming_movies VARCHAR
   contract VARCHAR  -- Month-to-month, One year, Two year
   paperless_billing VARCHAR
   payment_method VARCHAR
   monthly_charges FLOAT
   total_charges FLOAT

2) predictions
   id INT
   customer_id VARCHAR  -- joins customers.customer_id
   churn_probability FLOAT  -- 0 to 1
   predicted_churn VARCHAR  -- Yes or No
   risk_level VARCHAR  -- Low, Medium, High
   prediction_date DATETIME

3) segments
   customer_id VARCHAR PRIMARY KEY
   cluster_id INT
   segment_name VARCHAR

Risk levels are project-defined:
  Low: probability < 0.30
  Medium: 0.30 to 0.70 inclusive
  High: probability > 0.70
"""

SQL_SYSTEM_PROMPT = f"""You translate a manager/employee question into ONE read-only MySQL SELECT query.

Rules:
- Return ONLY SQL, no markdown, no commentary.
- Use SELECT or WITH ... SELECT only.
- Never use INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, REPLACE, GRANT, REVOKE, LOAD, INTO OUTFILE, or multiple statements.
- Prefer JOINs on customer_id when the question needs both features and predictions.
- Add LIMIT 50 unless the question is a COUNT/aggregate that returns a few rows.
- Use the exact column names from the schema.

Schema:
{SCHEMA_FOR_LLM}
"""

ANSWER_SYSTEM_PROMPT = """You are an assistant for a telecom churn prototype.
You receive a user question and the result of a read-only SQL query.
Answer in plain language using only that result.
If the result is empty, say so.
Do not invent customers or numbers.
Do not claim you predicted churn; you only summarized database values.
Keep the answer short.
"""
