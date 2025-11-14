import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
import os
import logging

load_dotenv()

POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_USER = os.getenv("POSTGRES_USER", "admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "admin")

if not POSTGRES_HOST or not POSTGRES_PORT or not POSTGRES_USER:
    raise RuntimeError("ENV variables are missing")

def create_logs_table():
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB
    )
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user_id BIGINT,
        is_authenticated BOOLEAN,
        telegram_id BIGINT,
        trace_id UUID,
        action VARCHAR(255),
        response_code INTEGER,
        request_method VARCHAR(50),
        request_body TEXT,
        platform VARCHAR(50),
        level VARCHAR(20),
        source VARCHAR(100),
        env VARCHAR(50),
        event_type VARCHAR(100),
        message TEXT
    )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    logging.info("Table 'logs' ensured in PostgreSQL.")

if __name__ == "__main__":
    create_logs_table()