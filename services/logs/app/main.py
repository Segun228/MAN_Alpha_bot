from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from .clickhouse_client import insert_log_async
import asyncio
import os
import logging
from .kafka_consumer import KafkaLogConsumer
from .init_clickhouse import create_logs_table
from dotenv import load_dotenv
from fastapi import Response
from prometheus_client import generate_latest, REGISTRY


from prometheus_client import Counter, Histogram, generate_latest, REGISTRY

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

KAFKA_LOGS_TOPIC = os.getenv("KAFKA_LOGS_TOPIC")


REQUEST_COUNT = Counter('bot_http_requests_total', 'Total Bot HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('bot_http_request_duration_seconds', 'Bot HTTP request duration')
BOT_KAFKA_MESSAGES = Counter('bot_kafka_messages_processed_total', 'Total Bot Kafka messages processed', ['topic', 'status'])

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_logs_table()
    logging.info("ClickHouse table ensured")

    bot_consumer = KafkaLogConsumer(KAFKA_LOGS_TOPIC, insert_log_async)
    await bot_consumer.start()
    logging.info("Kafka consumers started")

    bot_task = asyncio.create_task(bot_consumer.consume_forever())
    logging.info("Kafka consumer tasks running")

    try:
        yield
    finally:
        logging.info("Shutting down Kafka consumers...")
        await bot_consumer.stop()
        bot_task.cancel()
        logging.info("Kafka consumers stopped")

app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = asyncio.get_event_loop().time()
    
    response = await call_next(request)
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    duration = asyncio.get_event_loop().time() - start_time
    REQUEST_DURATION.observe(duration)
    
    return response


@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(REGISTRY),
        media_type="text/plain"
    )



@app.get("/")
def ping():
    return {"status": "Kafka BOT consumer is alive"}