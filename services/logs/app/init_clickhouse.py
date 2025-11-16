from clickhouse_driver import Client
import clickhouse_connect
from clickhouse_connect.driver.exceptions import OperationalError
from dotenv import load_dotenv
import os
import logging
import time

load_dotenv()

def get_clickhouse_client():
    """
    Создает клиент ClickHouse с повторными попытками подключения
    """
    max_retries = 5
    retry_delay = 5
    
    host = os.getenv("CLICKHOUSE_HOST")
    port = os.getenv("CLICKHOUSE_HTTP_PORT")
    username = os.getenv("CLICKHOUSE_USER", "default")
    password = os.getenv("CLICKHOUSE_PASSWORD", "")

    if not host or not port or not username:
        raise RuntimeError("ENV variables are missing")

    for attempt in range(max_retries):
        try:
            logging.info(f"🔄 Connecting to ClickHouse at {host}:{port} (attempt {attempt + 1}/{max_retries})")
            
            client = clickhouse_connect.get_client(
                host=host, 
                port=int(port), 
                username=username, 
                password=password
            )
            client.command("SELECT 1")
            logging.info("✅ ClickHouse connection successful")
            return client
            
        except OperationalError as e:
            logging.warning(f"⚠️ ClickHouse connection failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                logging.info(f"🔄 Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logging.error("❌ Failed to connect to ClickHouse after all retries")
                raise

def create_logs_table():
    """
    Создает таблицу логов в ClickHouse
    """
    client = None
    try:
        client = get_clickhouse_client()
        if client is None:
            raise ValueError("Recieved client as None")

        client.command("""
        CREATE DATABASE IF NOT EXISTS logs_database
        """)

        client.command("""
        CREATE TABLE IF NOT EXISTS logs_database.logs (
            timestamp DateTime,
            user_id UInt64,
            is_authenticated UInt8,
            telegram_id String,
            trace_id String,
            action String,
            response_code UInt16,
            request_method String,
            request_body String,
            platform String,
            level String,
            source String,
            env String,
            event_type String,
            message String
        ) ENGINE = MergeTree()
        ORDER BY timestamp
        """)
        
        logging.info("✅ Table 'logs_database.logs' ensured.")
        
    except Exception as e:
        logging.error(f"❌ Failed to create logs table: {e}")
        raise
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    create_logs_table()