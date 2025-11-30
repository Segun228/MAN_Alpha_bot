from aiokafka import AIOKafkaProducer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import KafkaConnectionError
import json
import logging
import uuid
import os
import asyncio
from dotenv import load_dotenv
from datetime import datetime, timezone
from typing import Any

load_dotenv()

KAFKA_BROKER_DOCKER = os.getenv("KAFKA_BROKER_URL")
KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL")
KAFKA_TOPIC = os.getenv("KAFKA_LOGS_TOPIC")
PRODUCER_CLIENT_ID = os.getenv("PRODUCER_CLIENT_ID")
LOGS = os.getenv("LOGS", "false").lower() == "true"

if not KAFKA_BROKER_DOCKER:
    raise RuntimeError("KAFKA_BROKER_DOCKER not set in environment")

_producer = None

async def ensure_topic_exists(max_retries=5, retry_delay=5):
    if not LOGS:
        logging.warning("The logging mode is turned off")
        return
    
    admin_client = None
    for attempt in range(max_retries):
        try:
            if not KAFKA_BROKER_DOCKER:
                raise RuntimeError("KAFKA_BROKER_DOCKER not set in environment")
            
            admin_client = AIOKafkaAdminClient(
                bootstrap_servers=KAFKA_BROKER_DOCKER,
                client_id="admin_client",
                request_timeout_ms=10000
            )
            
            await admin_client.start()
            
            topic_list = [NewTopic(
                name=KAFKA_TOPIC,
                num_partitions=1,
                replication_factor=1
            )]

            try:
                await admin_client.create_topics(new_topics=topic_list)
                logging.info(f"Topic '{KAFKA_TOPIC}' created")
                break
            except Exception as e:
                if "TopicAlreadyExistsError" in str(e) or "already exists" in str(e):
                    logging.info(f"Topic '{KAFKA_TOPIC}' already exists")
                    break
                else:
                    raise e
                    
        except (KafkaConnectionError, ConnectionError) as e:
            logging.warning(f"Kafka connection failed (attempt {attempt + 1}/{max_retries}): {e}")
            if admin_client:
                await admin_client.close()
            if attempt < max_retries - 1:
                logging.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logging.error(f"Failed to connect to Kafka after {max_retries} attempts")
                raise
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            if admin_client:
                await admin_client.close()
            raise
        finally:
            if admin_client:
                await admin_client.close()



async def get_producer(max_retries=3, retry_delay=2):
    global _producer
    if not LOGS:
        return None
    if not KAFKA_BROKER_DOCKER:
        raise RuntimeError("KAFKA_BROKER_DOCKER not set in environment")
    if _producer is None:
        for attempt in range(max_retries):
            try:
                _producer = AIOKafkaProducer(
                    bootstrap_servers=KAFKA_BROKER_DOCKER,
                    client_id=PRODUCER_CLIENT_ID,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    request_timeout_ms=10000
                )
                await _producer.start()
                logging.info("Kafka producer connected successfully")
                break
            except (KafkaConnectionError, ConnectionError) as e:
                logging.warning(f"Kafka producer connection failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    logging.error("Kafka producer unavailable after retries")
                    _producer = None
            except Exception as e:
                logging.error(f"Unexpected producer error: {e}")
                _producer = None
                break
    return _producer


async def build_log_message(
    telegram_id:str|None|int,
    action:str|None,
    source:str|None,
    payload:str|None|Any=None,
    platform:str|None="business_analyser",
    level:str|None="INFO",
    env:str|None="prod",
    timestamp=None,
    request_method:int|str|None=None,
    request_body:str|None=None,
    response_code:int|None=None,
    user_id:int|str|None=None,
    is_authenticated:bool|None=False
):
    if not LOGS:
        return {"status": "skipped", "reason": "logging_disabled"}
    
    message = {
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "trace_id": str(uuid.uuid4()),
        "user_id": user_id,
        "is_authenticated": is_authenticated,
        "telegram_id": telegram_id,
        "platform": platform,
        "action": action,
        "request_method": request_method,
        "request_body": request_body,
        "response_code": response_code,
        "level": level,
        "event_type": action,
        "source": source,
        "env": env,
        "message": f"User {telegram_id} performed {action}",
    }
    return await send_to_kafka(message)

async def send_to_kafka(data):
    if not LOGS:
        return {"status": "skipped", "reason": "logging_disabled"}
        
    producer = await get_producer()
    if producer is None:
        logging.info(f"Kafka not available, skipping log: {data}")
        return {"status": "skipped", "reason": "producer_unavailable"}

    try:
        messages = []
        
        if isinstance(data, list):
            for item in data:
                if hasattr(item, "dict"):
                    item = item.dict()
                messages.append(item)
                await producer.send_and_wait(KAFKA_TOPIC, value=item)
        else:
            if hasattr(data, "dict"):
                data = data.dict()
            messages.append(data)
            await producer.send_and_wait(KAFKA_TOPIC, value=data)

        result = {
            "status": "success",
            "messages_sent": len(messages),
            "sample": messages[0] if messages else None,
        }
        logging.info(f"Logged {len(messages)} messages to Kafka successfully!")
        return result

    except Exception as e:
        logging.error(f"Failed to send to Kafka: {e}")
        return {"status": "failed", "error": str(e)}

async def close_producer():
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None


def build_log_message_sync(
    telegram_id,
    action,
    source,
    payload=None,
    platform="bot",
    level="INFO",
    env="prod",
    timestamp=None
):
    if not LOGS:
        return {"status": "skipped", "reason": "logging_disabled"}
    
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(
        build_log_message(telegram_id, action, source, payload, platform, level, env, timestamp)
    )


async def init_kafka():
    if not LOGS:
        return
    asyncio.create_task(_background_kafka_init())

async def _background_kafka_init():
    """Фоновая инициализация Kafka без блокировки бота"""
    try:
        await ensure_topic_exists(max_retries=3, retry_delay=2)
        await get_producer(max_retries=2, retry_delay=1)
        logging.info("✅ Kafka инициализирована в фоне")
    except Exception as e:
        logging.warning(f"⚠️ Kafka не инициализирована: {e}. Бот работает без логирования в Kafka")
