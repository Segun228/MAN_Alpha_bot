import os
import json
import uuid
import logging
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
import asyncio
import csv
import io


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

async def insert_message_async(message: dict):
    timestamp = parse_timestamp(message.get('timestamp'))

    try:
        await asyncio.get_event_loop().run_in_executor(None, lambda: _insert_message_sync(message, timestamp))
        logging.info(f"Inserted message: {message.get('trace_id')}")
    except Exception:
        logging.exception(f"Failed to insert message: {message}")

def _insert_message_sync(message: dict, timestamp: datetime):
    """Синхронная функция для вставки в таблицу Messages"""
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
            INSERT INTO Messages (
                timestamp, telegram_id, message_id, direction, message, chat_type, business_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            timestamp,
            safe_int(message.get('telegram_id')),
            safe_int(message.get('message_id')),
            str(message.get('direction', 'question')),
            str(message.get('message', '')),
            str(message.get('chat_type', 'private')),
            message.get('business_id'),
        ))
        conn.commit()
        logging.info("Message inserted sucessfully")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()



def get_user_messages(
    telegram_id: int, 
    offset: int|None = None, 
    business_id: int|None = None
):
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DBNAME,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    cursor = conn.cursor()
    try:
        if business_id:
            if offset:
                cursor.execute("""
                    SELECT timestamp, telegram_id, message_id, direction, message, chat_type
                    FROM Messages
                    WHERE telegram_id = %s AND business_id = %s
                    ORDER BY timestamp DESC
                    offset %s
                """, (telegram_id, business_id, offset))
            else:
                cursor.execute("""
                    SELECT timestamp, telegram_id, message_id, direction, message, chat_type
                    FROM Messages
                    WHERE telegram_id = %s AND business_id = %s
                    ORDER BY timestamp DESC
                """, (telegram_id, business_id))
        else:
            if offset:
                cursor.execute("""
                    SELECT timestamp, telegram_id, message_id, direction, message, chat_type
                    FROM Messages
                    WHERE telegram_id = %s
                    ORDER BY timestamp DESC
                    offset %s
                """, (telegram_id, offset))
            else:
                cursor.execute("""
                    SELECT timestamp, telegram_id, message_id, direction, message, chat_type
                    FROM Messages
                    WHERE telegram_id = %s
                    ORDER BY timestamp DESC
                """, (telegram_id,))
        rows = cursor.fetchall()
        messages = []
        for row in rows:
            message = {
                'timestamp': row[0],
                'telegram_id': row[1],
                'message_id': row[2],
                'direction': row[3],
                'message': row[4],
                'chat_type': row[5]
            }
            messages.append(message)
        return messages
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()




def get_user_messages_csv(telegram_id: int, offset: int|None = None)->io.BytesIO:
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DBNAME,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    cursor = conn.cursor()
    try:
        if offset:
            cursor.execute("""
                SELECT timestamp, telegram_id, message_id, direction, message, chat_type
                FROM Messages
                WHERE telegram_id = %s
                ORDER BY timestamp DESC
                OFFSET %s
            """, (telegram_id, offset))
        else:
            cursor.execute("""
                SELECT timestamp, telegram_id, message_id, direction, message, chat_type
                FROM Messages
                WHERE telegram_id = %s
                ORDER BY timestamp DESC
            """, (telegram_id,))
        
        rows = cursor.fetchall()
        
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        
        writer.writerow(['timestamp', 'telegram_id', 'message_id', 'direction', 'message', 'chat_type'])
        
        for row in rows:
            writer.writerow(row)
        
        output.seek(0)
        
        csv_bytes = io.BytesIO()
        csv_bytes.write(output.getvalue().encode('utf-8'))
        csv_bytes.seek(0)
        
        return csv_bytes
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()