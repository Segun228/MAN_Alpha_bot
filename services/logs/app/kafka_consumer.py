import json
import os
from aiokafka import AIOKafkaConsumer
from dotenv import load_dotenv
import logging
import asyncio

from prometheus_client import Counter, Histogram

load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")

KAFKA_MESSAGES_PROCESSED = Counter('kafka_messages_processed_total', 'Total Kafka messages processed', ['topic', 'status'])
KAFKA_PROCESSING_DURATION = Histogram('kafka_processing_duration_seconds', 'Kafka message processing duration')
KAFKA_CONSUMER_ERRORS = Counter('kafka_consumer_errors_total', 'Kafka consumer errors', ['topic'])

class KafkaLogConsumer:
    def __init__(self, topic, insert_log):
        if not KAFKA_BOOTSTRAP_SERVERS:
            raise Exception("empty bootstrap server env variable given")
        self.topic = topic
        self.insert_log = insert_log
        self.consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )

    async def start(self):
        await self.consumer.start()
        logging.info(f"Kafka consumer started for topic: {self.topic}")

    async def consume_forever(self):
        try:
            while True:
                msg = await self.consumer.getone()
                await self.process_message(msg)
        except asyncio.CancelledError:
            logging.info(f"Kafka consumer task cancelled for topic: {self.topic}")
            raise 
        except Exception as e:
            logging.error(f"Kafka error in topic {self.topic}: {e}")
            logging.exception("Kafka consumer crashed")

    async def stop(self):
        await self.consumer.stop()
        logging.info(f"Kafka consumer stopped for topic: {self.topic}")

    async def process_message(self, message):
        start_time = asyncio.get_event_loop().time()
        try:
            await self.insert_log(message.value)
            KAFKA_MESSAGES_PROCESSED.labels(topic=self.topic, status='success').inc()
        except Exception as e:
            KAFKA_MESSAGES_PROCESSED.labels(topic=self.topic, status='error').inc()
            KAFKA_CONSUMER_ERRORS.labels(topic=self.topic).inc()
            logging.error(f"Error processing Kafka message: {e}")
            raise e
        finally:
            duration = asyncio.get_event_loop().time() - start_time
            KAFKA_PROCESSING_DURATION.observe(duration)