from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import asyncio
import os
import logging
from dotenv import load_dotenv
from fastapi import Response
from prometheus_client import generate_latest, REGISTRY
from .kafka_producer import ensure_topic_exists, build_log_message
import json
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
from fastapi import Request
from .recomendations import generate_recomendation
from .app_requests import get_summary
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse


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
    await ensure_topic_exists()
    try:
        yield
    finally:
        logging.info("Shutting down summarizer...")



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




@app.post("/recomedations")
async def recomedations(request: Request):
    try:
        data = await request.json()
        context = data.get("context")
        business = data.get("business", "Малый бизнес")
        description = data.get("description")
        if not context:
            raise HTTPException(
                status_code=400,
                detail="Empty context given"
            )
        await build_log_message(
            telegram_id = data.get("telegram_id"),
            action = data.get("action"),
            source = data.get("source"),
            payload = data.get("payload"),
            platform = data.get("platform", "bot"),
            level = data.get("level", "INFO"),
            env = data.get("env", "prod"),
            timestamp = data.get("timestamp", "prod"),
            request_method = data.get("request_method", "post"),
            request_body = "ping",
            response_code = 200,
            user_id = data.get("user_id"),
            is_authenticated = True
        )
        summary = await get_summary(
            context = context,
            business = business,
            description = description,
        )
        result = generate_recomendation(
            summary = summary,
            words_count = data.get("words_count", None)
        )
        return JSONResponse(
            content=result,
            media_type="text/plain"
        )
    except Exception as e:
        logging.exception(e)
        return Response(status_code=500)



@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(REGISTRY),
        media_type="text/plain"
    )



@app.get("/")
async def ping(request: Request):
    return {"status": "Recomendator is alive"}