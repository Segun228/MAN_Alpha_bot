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
import uuid
from contextvars import ContextVar

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

KAFKA_MESSAGES_TOPIC = os.getenv("KAFKA_MESSAGES_TOPIC")
KAFKA_GRADES_TOPIC = os.getenv("KAFKA_GRADES_TOPIC")


REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')


request_id_var: ContextVar[str] = ContextVar('request_id', default='')

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("🚀 Starting application lifespan")
    
    try:
        create_grades_table()
        create_messages_table()
        logging.info("✅ Postgres tables ensured")
        
        messages_consumer = None
        grades_consumer = None
        message_task = None
        grades_task = None
        
        messages_consumer = KafkaLogConsumer(KAFKA_MESSAGES_TOPIC, insert_message_async)
        await messages_consumer.start()
        logging.info(f"✅ Kafka consumer started for topic: {KAFKA_MESSAGES_TOPIC}")
        message_task = asyncio.create_task(messages_consumer.consume_forever())

        grades_consumer = KafkaLogConsumer(KAFKA_GRADES_TOPIC, insert_grade_async)
        await grades_consumer.start()
        logging.info(f"✅ Kafka consumer started for topic: {KAFKA_GRADES_TOPIC}")
        grades_task = asyncio.create_task(grades_consumer.consume_forever())
        
        logging.info("🎉 All Kafka consumers started successfully")
        yield
        
    except Exception as e:
        logging.error(f"❌ Error starting Kafka consumers: {e}", exc_info=True)
        raise
    finally:
        logging.info("🛑 Shutting down Kafka consumers...")
        if message_task:
            message_task.cancel()
            logging.info("📝 Message consumer task cancelled")
        if grades_task:
            grades_task.cancel()
            logging.info("⭐ Grades consumer task cancelled")
        if messages_consumer:
            await messages_consumer.stop()
            logging.info("📝 Message consumer stopped")
        if grades_consumer:
            await grades_consumer.stop()
            logging.info("⭐ Grades consumer stopped")
        logging.info("✅ All Kafka consumers stopped")

app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    request_id_var.set(request_id)
    
    start_time = asyncio.get_event_loop().time()
    
    logging.info(f"📥 [{request_id}] {request.method} {request.url.path} - Request started")
    
    try:
        response = await call_next(request)
        
        duration = (asyncio.get_event_loop().time() - start_time) * 1000  # Convert to ms
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        REQUEST_DURATION.observe(duration / 1000)  # Keep in seconds for Prometheus
        
        logging.info(f"📤 [{request_id}] {request.method} {request.url.path} - Response: {response.status_code} - Duration: {duration:.2f}ms")
        
        return response
        
    except Exception as e:
        duration = (asyncio.get_event_loop().time() - start_time) * 1000
        logging.error(f"💥 [{request_id}] {request.method} {request.url.path} - Error: {e} - Duration: {duration:.2f}ms", exc_info=True)
        raise


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
async def insert_grade(grade: Grade):
    request_id = request_id_var.get()
    logging.info(f"⭐ [{request_id}] Inserting grade for user: {grade.telegram_id}")
    
    try:
        grade_data = {
            'telegram_id': grade.telegram_id,
            'service_grade': grade.service_grade,
            'model_grade': grade.model_grade,
            'overall_grade': grade.overall_grade,
            'message': grade.message or ''
        }
        
        logging.info(f"📊 [{request_id}] Grade data: {grade_data}")
        
        await asyncio.get_event_loop().run_in_executor(
            None, 
            _insert_grade_sync, 
            grade_data, 
            datetime.now()
        )
        
        logging.info(f"✅ [{request_id}] Grade saved successfully for user: {grade.telegram_id}")
        return {"status": "success", "message": "Grade saved"}
        
    except Exception as e:
        logging.error(f"❌ [{request_id}] Error saving grade for user {grade.telegram_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save grade"
        )


@app.post("/messages")
async def insert_message(message: MessageRequest):
    request_id = request_id_var.get()
    logging.info(f"📝 [{request_id}] Inserting {message.direction} message for user: {message.telegram_id}, message_id: {message.message_id}")
    
    try:
        if message.direction not in ['question', 'answer']:
            logging.warning(f"⚠️ [{request_id}] Invalid direction: {message.direction}")
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
        
        logging.info(f"💬 [{request_id}] Message data: {message_data}")
        
        await asyncio.get_event_loop().run_in_executor(
            None, 
            _insert_message_sync, 
            message_data, 
            datetime.now()
        )
        
        logging.info(f"✅ [{request_id}] {message.direction.capitalize()} message saved successfully for user: {message.telegram_id}")
        return {"status": "success", "message": "Message saved"}
        
    except HTTPException:
        logging.warning(f"⚠️ [{request_id}] HTTPException for message insert: user {message.telegram_id}")
        raise
    except Exception as e:
        logging.error(f"❌ [{request_id}] Error saving message for user {message.telegram_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save message"
        )


@app.get("/messages/{telegram_id}")
async def get_user_mes(
    request: Request,
    telegram_id: int = Path(..., ge=1, description="ID пользователя"),
):
    request_id = request_id_var.get()
    logging.info(f"🔍 [{request_id}] Getting messages for user: {telegram_id}")
    
    try:
        load_dotenv()
        BOT_API_KEY = os.getenv("BOT_API_KEY")
        if not BOT_API_KEY:
            logging.error(f"❌ [{request_id}] BOT_API_KEY not found in environment")
            raise ValueError("BOT_API_KEY was not provided in env")
        
        headers = request.headers
        auth_header = headers.get("X-Bot-Key")
        
        if not auth_header or auth_header.strip() != BOT_API_KEY.strip():
            logging.warning(f"🔐 [{request_id}] Invalid API key attempt for user: {telegram_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
            
        logging.info(f"🔑 [{request_id}] API key validation successful for user: {telegram_id}")
            
        # Get offset from request body
        try:
            request_body = await request.json()
            offset = request_body.get("offset")
            if offset:
                offset = int(offset)
                logging.info(f"📄 [{request_id}] Using offset: {offset}")
            else:
                offset = None
        except Exception as e:
            logging.warning(f"⚠️ [{request_id}] Error parsing request body: {e}")
            offset = None

        result = get_user_messages(
            telegram_id=telegram_id,
            offset=offset
        )
        
        if not result:
            logging.info(f"📭 [{request_id}] No messages found for user: {telegram_id}")
            return {"status": "success", "data": []}
            
        logging.info(f"✅ [{request_id}] Found {len(result)} messages for user: {telegram_id}")
        return {"status": "success", "data": result}
        
    except HTTPException as e:
        logging.error(f"🚫 [{request_id}] HTTPException for user {telegram_id}: {e.detail}")
        raise
    except Exception as e:
        logging.error(f"❌ [{request_id}] Error getting messages for user {telegram_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get messages"
        )



@app.get("/messages/{telegram_id}/csv")
async def get_user_mes(
    request: Request,
    telegram_id: int = Path(..., ge=1, description="ID пользователя"),
):
    request_id = request_id_var.get()
    logging.info(f"🔍 [{request_id}] Getting messages for user: {telegram_id}")
    
    try:
        load_dotenv()
        BOT_API_KEY = os.getenv("BOT_API_KEY")
        if not BOT_API_KEY:
            logging.error(f"❌ [{request_id}] BOT_API_KEY not found in environment")
            raise ValueError("BOT_API_KEY was not provided in env")
        
        headers = request.headers
        auth_header = headers.get("X-Bot-Key")
        
        if not auth_header or auth_header.strip() != BOT_API_KEY.strip():
            logging.warning(f"🔐 [{request_id}] Invalid API key attempt for user: {telegram_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
            
        logging.info(f"🔑 [{request_id}] API key validation successful for user: {telegram_id}")
            
        # Get offset from request body
        try:
            request_body = await request.json()
            offset = request_body.get("offset")
            if offset:
                offset = int(offset)
                logging.info(f"📄 [{request_id}] Using offset: {offset}")
            else:
                offset = None
        except Exception as e:
            logging.warning(f"⚠️ [{request_id}] Error parsing request body: {e}")
            offset = None

        result = get_user_messages(
            telegram_id=telegram_id,
            offset=offset
        )
        
        if not result:
            logging.info(f"📭 [{request_id}] No messages found for user: {telegram_id}")
            return {"status": "success", "data": []}
            
        logging.info(f"✅ [{request_id}] Found {len(result)} messages for user: {telegram_id}")
        return {"status": "success", "data": result}
        
    except HTTPException as e:
        logging.error(f"🚫 [{request_id}] HTTPException for user {telegram_id}: {e.detail}")
        raise
    except Exception as e:
        logging.error(f"❌ [{request_id}] Error getting messages for user {telegram_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get messages"
        )



@app.get("/metrics")
async def metrics():
    request_id = request_id_var.get()
    logging.info(f"📊 [{request_id}] Metrics endpoint accessed")
    return Response(
        content=generate_latest(REGISTRY),
        media_type="text/plain"
    )

@app.get("/")
def ping():
    logging.info("🏓 Health check endpoint accessed")
    return {
        "status": "ok",
        "text": "DB_service is alive"
    }