-- Runs once when the MySQL container is first created.
-- Creates a SELECT-only chatbot user. Tables are created by SQLAlchemy on backend startup,
-- then seed.py grants SELECT on the analytics tables (not the users table).

CREATE USER IF NOT EXISTS 'chatbot_user'@'%' IDENTIFIED BY 'change_this_chatbot_password';

-- Temporary broad SELECT on the database so the user exists even before tables are created.
-- Seed script immediately REVOKE this and GRANT table-level SELECT instead.
GRANT SELECT ON churn_db.* TO 'chatbot_user'@'%';
FLUSH PRIVILEGES;
