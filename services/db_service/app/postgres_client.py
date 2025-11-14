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

async def insert_log_async(log: dict):
    timestamp = parse_timestamp(log.get('timestamp'))

    try:
        await asyncio.get_event_loop().run_in_executor(None, lambda: _insert_log_sync(log, timestamp))
        logging.info(f"Inserted log: {log.get('trace_id')}")
    except Exception:
        logging.exception(f"Failed to insert log: {log}")

def _insert_log_sync(log: dict, timestamp: datetime):
    """Синхронная функция для вставки в PostgreSQL"""
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
            INSERT INTO logs (
                timestamp, user_id, is_authenticated, telegram_id, trace_id,
                action, response_code, request_method, request_body,
                platform, level, source, env, event_type, message
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            timestamp,
            safe_int(log.get('user_id')),
            bool(log.get('is_authenticated', False)),
            str(log.get('telegram_id', '')),
            str(log.get('trace_id', str(uuid.uuid4()))),
            str(log.get('action', '')),
            safe_int(log.get('response_code', 200)),
            str(log.get('request_method', 'GET')),
            str(log.get('request_body', '')),
            str(log.get('platform', 'backend')),
            str(log.get('level', 'INFO')),
            str(log.get('source', 'backend')),
            str(log.get('env', 'prod')),
            str(log.get('event_type', log.get('action', 'action'))),
            str(log.get('message', 'undefined action'))
        ))
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()