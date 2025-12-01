import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
import os
import logging

load_dotenv()

POSTGRES_DBNAME = os.getenv("POSTGRES_DBNAME")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_USER = os.getenv("POSTGRES_USER", "user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password123")

if not POSTGRES_HOST or not POSTGRES_PORT or not POSTGRES_USER:
    raise RuntimeError("ENV variables are missing")

def create_messages_table():
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DBNAME
    )
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Messages (
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        telegram_id BIGINT,
        message_id BIGINT,
        direction VARCHAR(10) CHECK (direction IN ('question', 'answer')),
        message TEXT,
        business_id INTEGER DEFAULT NULL,
        chat_type VARCHAR(100)
    );
    """)
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("Table 'Messages' ensured in PostgreSQL.")


def create_grades_table():
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DBNAME
    )
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Grades (
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        telegram_id BIGINT,
        service_grade INT CHECK (service_grade >= 0 AND service_grade <= 5),
        model_grade INT CHECK (model_grade >= 0 AND model_grade <= 5),
        overall_grade INT CHECK (overall_grade >= 0 AND overall_grade <= 5),
        message TEXT
    )
    """)
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("Table 'Grades' ensured in PostgreSQL.")


if __name__ == "__main__":
    create_messages_table()
    create_grades_table()