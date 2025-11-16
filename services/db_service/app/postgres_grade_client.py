import os
import json
import uuid
import logging
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
import asyncio

load_dotenv()

POSTGRES_DBNAME = os.getenv("POSTGRES_DBNAME")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_USER = os.getenv("POSTGRES_USER", "user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password123")

if not POSTGRES_HOST:
    raise RuntimeError("POSTGRES_HOST not set in env")

def parse_timestamp(ts):
    if ts is None:
        return datetime.utcnow()
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            logging.warning(f"Failed to parse timestamp: {ts}")
            return datetime.utcnow()
    return datetime.utcnow()

def serialize_field(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value)

def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

async def insert_grade_async(grade: dict):
    timestamp = parse_timestamp(grade.get('timestamp'))

    try:
        await asyncio.get_event_loop().run_in_executor(None, lambda: _insert_grade_sync(grade, timestamp))
        logging.info(f"Inserted grade: {grade.get('trace_id')}")
    except Exception:
        logging.exception(f"Failed to insert grade: {grade}")

def _insert_grade_sync(grade: dict, timestamp: datetime):
    """Синхронная функция для вставки в таблицу Grades"""
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DBNAME,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO Grades (
                timestamp, telegram_id, service_grade, model_grade, overall_grade, message
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            timestamp,
            safe_int(grade.get('telegram_id')),
            safe_int(grade.get('service_grade')),
            safe_int(grade.get('model_grade')),
            safe_int(grade.get('overall_grade')),
            str(grade.get('message', ''))
        ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()