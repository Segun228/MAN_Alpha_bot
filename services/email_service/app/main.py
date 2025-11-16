from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import asyncio
import os
import logging
from .kafka_consumer import KafkaLogConsumer
from dotenv import load_dotenv
from fastapi import Response
from prometheus_client import generate_latest, REGISTRY
from fastapi import File, UploadFile, Form
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from prometheus_client import Counter, Histogram
from app.email import send_email
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

KAFKA_LOGS_TOPIC = os.getenv("KAFKA_LOGS_TOPIC")


REQUEST_COUNT = Counter('bot_http_requests_total', 'Total Bot HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('bot_http_request_duration_seconds', 'Bot HTTP request duration')
BOT_KAFKA_MESSAGES = Counter('bot_kafka_messages_processed_total', 'Total Bot Kafka messages processed', ['topic', 'status'])


SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = os.getenv("SMTP_PORT", 587)
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")


if SMTP_SERVER is None:
    raise ValueError("SMTP_SERVER не задан в переменных окружения")
if SMTP_PORT is None:
    raise ValueError("SMTP_PORT не задан в переменных окружения")
if SENDER_EMAIL is None:
    raise ValueError("SENDER_EMAIL не задан в переменных окружения")
if SENDER_PASSWORD is None:
    raise ValueError("SENDER_PASSWORD не задан в переменных окружения")

try:
    SMTP_PORT = int(SMTP_PORT)
except (TypeError, ValueError):
    raise ValueError(f"SMTP_PORT должен быть числом, получено: {SMTP_PORT}")

app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("ClickHouse table ensured")
    bot_consumer = KafkaLogConsumer(KAFKA_LOGS_TOPIC, send_email)
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


@app.post("/send-email/")
async def send_email_with_zip(
    text_message: str = Form(...),
    zip_file: UploadFile = File(...),
    receiver_email: str = Form(...),
    subject: str = Form("Фото архив")
):
    """
    Получает ZIP файл и текст из multipart/form-data и отправляет по почте
    """
    try:
        if SMTP_SERVER is None:
            raise ValueError("SMTP_SERVER не задан в переменных окружения")
        if SMTP_PORT is None:
            raise ValueError("SMTP_PORT не задан в переменных окружения")
        if SENDER_EMAIL is None:
            raise ValueError("SENDER_EMAIL не задан в переменных окружения")
        if SENDER_PASSWORD is None:
            raise ValueError("SENDER_PASSWORD не задан в переменных окружения")
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(text_message, 'plain'))
        zip_content = await zip_file.read()
        zip_part = MIMEBase('application', 'zip')
        zip_part.set_payload(zip_content)
        encoders.encode_base64(zip_part)
        zip_part.add_header(
            'Content-Disposition',
            f'attachment; filename="{zip_file.filename}"'
        )
        msg.attach(zip_part)
        with smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT)) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        logging.info(f"Письмо с архивом '{zip_file.filename}' успешно отправлено на {receiver_email}")
        return {
            "status": "success",
            "message": f"Письмо с архивом '{zip_file.filename}' успешно отправлено на {receiver_email}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Ошибка при отправке письма: {str(e)}"
        }


@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(REGISTRY),
        media_type="text/plain"
    )


@app.get("/health")
def ping():
    return {"status": "ok"}