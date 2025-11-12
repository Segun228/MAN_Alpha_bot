import os
import json
import uuid
import logging
from datetime import datetime
from dotenv import load_dotenv
import clickhouse_connect

load_dotenv()

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_HTTP_PORT", 8123))
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "user")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "password123")

if not CLICKHOUSE_HOST:
    raise RuntimeError("CLICKHOUSE_HOST not set in env")



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

    data_row = [
        timestamp,
        safe_int(log.get('user_id')),
        1 if log.get('is_authenticated') else 0,
        str(log.get('telegram_id')),
        str(serialize_field(log.get("trace_id", str(uuid.uuid4())))),
        str(serialize_field(log.get('action'))),
        safe_int(log.get('response_code', 200)),
        str(serialize_field(log.get('request_method', 'GET'))),
        str(serialize_field(log.get('request_body'))),
        str(serialize_field(log.get('platform', 'backend'))),
        str(serialize_field(log.get('level', 'INFO'))),
        str(serialize_field(log.get('source', 'backend'))),
        str(serialize_field(log.get('env', 'prod'))),
        str(serialize_field(log.get('event_type', log.get('action', 'action')))),
        str(serialize_field(log.get("message", "undefined action")))
    ]

    try:
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: clickhouse_connect.get_client(
            host=CLICKHOUSE_HOST,
            port=CLICKHOUSE_PORT,
            username=CLICKHOUSE_USER,
            password=CLICKHOUSE_PASSWORD
        ).insert(
            table='logs_database.logs',
            data=[data_row],
            column_names=[
                'timestamp', 'user_id', 'is_authenticated', 'telegram_id', 'trace_id',
                'action', 'response_code', 'request_method', 'request_body',
                'platform', 'level', 'source', 'env', 'event_type', 'message'
            ]
        ))
        logging.info(f"Inserted log: {log.get('trace_id')}")
    except Exception:
        logging.exception(f"Failed to insert log: {log}")