import logging
import os
from contextlib import asynccontextmanager
from typing import List
import re
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import aiohttp

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        logging.info("Shutting down chat model...")


api_key = os.getenv("CONVERSATION_MODEL_API_KEY")
URL = os.getenv("OPENROUTER_URL")
if URL == "http://model-service:8095/api/v1/chat/completions":
    model_name = "Qwen2.5-3B-Instruct(local)"
else:
    model_name = "meta-llama/llama-3.1-8b-instruct"

app = FastAPI(lifespan=lifespan)

if not URL:
    raise ValueError("URL route is not set in .env")

if not api_key:
    raise ValueError("api-key is not set in .env")


class Message(BaseModel):
    role: str
    content: str


class Context(BaseModel):
    history: List[Message] = []


class RequestData(BaseModel):
    text: str
    context: Context
    business: str = "малый бизнес"
    extended_data: str = ""
    word_count: int | None = None


ANSWER_EXAMPLE = """Анализ ситуации
                    - Краткая оценка текущей позиции
                    - Ключевые факторы влияния

                    Цели переговоров  
                    - Основная цель
                    - Второстепенные цели
                    - Минимально приемлемый результат

                    Стратегия переговоров
                    - Рекомендуемый подход
                    - План действий по этапам
                    - Переговорные техники

                    Ключевые аргументы
                    - Не более 5 основных тезисов
                    - Подкрепление фактами/цифрами
                    - Эмоциональные якоря

                    Риски и альтернативы
                    - Основные риски
                    - План Б
                    - Точки уступок

                    Практические рекомендации
                    - Что говорить/не говорить
                    - Подготовительные шаги"""


def build_system_prompt(request_data: RequestData):
    business_desc = f"Тип бизнеса: {request_data.business}"
    
    if request_data.extended_data:
        extended_desc = f"Дополнительные детали: {request_data.extended_data[:500]}"
    else:
        extended_desc = "Обязательно будь вежливым и профессиональным."
    
    word_limit = f"Ответ обязательно должен быть не длинее: {request_data.word_count} слов" if request_data.word_count else "Будь лаконичным"
    
    system_content = f"""Ты — эксперт по переговорам и консультант для среднего и малого бизнеса.

                        {business_desc}
                        {extended_desc}

                        ## Формат ответа:
                        {ANSWER_EXAMPLE}

                        ## Требования:
                        - {word_limit}
                        - Сохраняй реалистичность и практическую применимость
                        - Предлагай проверяемые решения
                        - Не нарушай законодательство РФ
                        - Всегда упоминай, что информацию необходимо проверять самостоятельно
                        - Будь профессиональным, но доступным для понимания"""

    return {
        "role": "system",
        "content": system_content.strip()
    }


@app.post("/generate_conversation")
async def generate_message(request_data: RequestData):
    text = request_data.text
    cleaned = re.sub(r'\s+', ' ', text.strip())
    if len(cleaned) < 3:
        return {
            "success": True,
            "response": "Пожалуйста, напишите более ёмкое сообщение",
            "usage": 0,
            "model": "-"
        }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-app.com",
        "X-Title": "conversationbot",
    }
    system_message = build_system_prompt(request_data)
    if request_data.word_count:
        user_message = {"role": "user", "content": request_data.text + f"ответь примерно за {request_data.word_count} слов"}
    else:
        user_message = {"role": "user", "content": request_data.text}
    messages = [system_message] + [message.dict() for message in request_data.context.history] + [user_message]
    try:
        data = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.8
        }

        timeout = aiohttp.ClientTimeout(
            total=300,
            connect=300,
            sock_connect=300,
            sock_read=300,
        )

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(URL, headers=headers, json=data) as resp:
                resp.raise_for_status()
                response_data = await resp.json()

        return {
            "success": True,
            "response": response_data["choices"][0]["message"]["content"],
            "usage": response_data.get("usage", {}),
            "model": response_data.get("model")
        }
    except aiohttp.ClientError as e:
        logging.exception(e)
        raise HTTPException(status_code=500, detail=f"Ошибка при запросе: {str(e)}")
    except Exception as e:
        logging.exception(e)
        raise HTTPException(status_code=500, detail=f"Неожиданная ошибка: {str(e)}")


@app.get("/model_health")
async def health_check():
    if api_key and URL:
        return {"message": "Conversation analyzer API is running", "status": "ok"}
    return {"message": "Conversation analyzer API key or URL not set", "status": "failed"}


@app.get("/")
async def root():
    if api_key and URL:
        return {"message": "Conversation analyzer API is running", "status": "ok"}
    return {"message": "Conversation analyzer API key or URL not set", "status": "failed"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8090)