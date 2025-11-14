from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from app.postgres_message_client import insert_message_async
from app.postgres_grade_client import insert_grade_async
import asyncio
import os
import logging
from app.kafka_consumer import KafkaLogConsumer
from app.init_postgres import create_grades_table, create_messages_table
from dotenv import load_dotenv
from fastapi import Response
from prometheus_client import generate_latest, REGISTRY
from fastapi import HTTPException, status, Path
from pydantic import BaseModel, Field
from typing import Optional, Literal
from prometheus_client import Counter, Histogram
from datetime import datetime
from app.postgres_grade_client import _insert_grade_sync
from app.postgres_message_client import _insert_message_sync, get_user_messages

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

KAFKA_MESSAGES_TOPIC = os.getenv("KAFKA_MESSAGES_TOPIC")
KAFKA_GRADES_TOPIC = os.getenv("KAFKA_GRADES_TOPIC")


REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_grades_table()
    create_messages_table()
    logging.info("Postgres table ensured")

    messages_consumer = KafkaLogConsumer(KAFKA_MESSAGES_TOPIC, insert_message_async)
    await messages_consumer.start()
    await messages_consumer.start()
    logging.info("Message kafka consumers started")
    message_task = asyncio.create_task(messages_consumer.consume_forever())
    logging.info("Kafka message consumer tasks running")

    grades_consumer = KafkaLogConsumer(KAFKA_MESSAGES_TOPIC, insert_grade_async)
    await grades_consumer.start()
    logging.info("Grades kafka consumers started")
    grades_task = asyncio.create_task(grades_consumer.consume_forever())
    logging.info("Kafka message consumer tasks running")
    try:
        yield
    finally:
        logging.info("Shutting down Kafka consumers...")
        await messages_consumer.stop()
        message_task.cancel()
        await grades_consumer.stop()
        grades_task.cancel()
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


class Grade(BaseModel):
    telegram_id: int
    service_grade: int = Field(ge=0, le=5)
    model_grade: int = Field(ge=0, le=5)
    overall_grade: int = Field(ge=0, le=5)
    message: Optional[str] = None


class MessageRequest(BaseModel):
    telegram_id: int
    message_id: int
    direction: Literal['question', 'answer']
    message: str
    chat_type: str = "private"


@app.post("/grades")
async def insert_grade(grade:Grade):
    try:
        grade_data = {
            'telegram_id': grade.telegram_id,
            'service_grade': grade.service_grade,
            'model_grade': grade.model_grade,
            'overall_grade': grade.overall_grade,
            'message': grade.message or ''
        }
        await asyncio.get_event_loop().run_in_executor(
            None, 
            _insert_grade_sync, 
            grade_data, 
            datetime.now()
        )
        return {"status": "success", "message": "Grade saved"}
    except Exception as e:
        logging.exception(f"Error saving grade: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save grade"
        )


@app.post("/messages")
async def insert_message(message: MessageRequest):
    try:
        if message.direction not in ['question', 'answer']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Direction must be 'question' or 'answer'"
            )
        message_data = {
            'telegram_id': message.telegram_id,
            'message_id': message.message_id,
            'direction': message.direction,
            'message': message.message,
            'chat_type': message.chat_type
        }
        await asyncio.get_event_loop().run_in_executor(
            None, 
            _insert_message_sync, 
            message_data, 
            datetime.now()
        )
        return {"status": "success", "message": "Message saved"}
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error saving message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save message"
        )


@app.get("/messages/{telegram_id}")
async def get_user_mes(
    request:Request,
    telegram_id: int = Path(..., ge=1, description="ID пользователя"),
):
    try:
        offset = request.get("offset")
        result = get_user_messages(
            telegram_id = telegram_id,
            offset = offset
        )
        if not result:
            raise Exception("Error while executing DB querry")
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error saving message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save message"
        )




@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(REGISTRY),
        media_type="text/plain"
    )

@app.get("/")
def ping():
    return {
        "status": "ok",
        "text":"DB_service is alive"
    }