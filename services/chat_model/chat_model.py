import logging
import os
from contextlib import asynccontextmanager
from typing import List

import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import aiohttp
import logging

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


api_key = os.getenv("OPENROUTER_API_KEY")
URL = os.getenv("OPENROUTER_URL")
app = FastAPI(lifespan=lifespan)

if not URL:  # Если .env заполнен неверно, завершаемся с адекватной ошибкой
    raise ValueError("URL route is not set in .env")

if not api_key:
    raise ValueError("api-key is not set in .env")


class Message(BaseModel):
    role: str  # Literal["user", "assistant"], можно внедрить после теста истории
    content: str


class Context(BaseModel):  # История - список сообщений по формату сверху
    history: List[Message] = []


class RequestData(BaseModel):
    text: str
    context: Context
    business: str = "малый бизнес"
    description: str = ""
    word_count: int | None = None


@app.post("/generate_response")
async def generate_message(request_data: RequestData):
    print(URL)
    if not request_data.text.strip():  # Сразу отлавливаю пустой случай
        return {
            "success": True,
            "response": "Пожалуйста, напишите более ёмкое сообщение",
            "usage": 0,
            "model": "-"
        }
        # Пытаюсь предугадать 2 случая, не требующих модели. Благодарность и приветствие. Можно добавить прощание
    if request_data.text.strip().lower() in ["привет", "здравствуй", "здравствуйте", "добрый день", "добрый вечер",
                                             "доброе утро", "хай", "здорова", "сап", "вассап", "васап"]:
        return {
            "success": True,
            "response": "Здравствуйте! Я многофункциональный бизнес-ассистент и буду всегда рад помочь Вам. "
                        "Помните, что я использую ИИ, поэтому проверяйте важную информацию перед принятием решений."
                        "Все мои ответы являются советами, которые могут требовать дополнительной оценки специалиста.",
            "usage": 0,
            "model": "-"
        }
    if request_data.text.strip().lower() in ["спасибо", "спс", "добро", "благодарю", "отлично", "класс", "кайф", "отл",
                                             "от души"]:
        return {
            "success": True,
            "response": "Отлично! Приятно быть полезным, буду рад помочь Вам снова!",
            "usage": 0,
            "model": "-"
        }
    headers = {  # Передаём апи-ключ в заголовок
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-app.com",
        "X-Title": "chatbot",
    }
    business_description = ""  # Создаём предложение с описанием бизнеса, если таковое имеется
    if request_data.description:
        business_description = "Более подробное описание бизнеса: " + request_data.description
    word_count_prompt = ""  # Создаём предложение с ограниченем слов, если оное присутствует
    if request_data.word_count:
        word_count_prompt = f"Ответ должен быть на {request_data.word_count} слов"
    system_message = {
        "role": "system",
        "content": f"Ты опытный бизнес-ассистент. Твоя задача дать точную консультацию для владельца {request_data.business}. "
                   f"{business_description}. Опирайся на существующий опыт и правила, не давай вредных и опасных советов. "
                   f"Не нарушай законодательство РФ и международные нормы. Упомянай, что информацию необходимо "
                   f"проверять самостоятельно." + word_count_prompt
    }
    user_message = {"role": "user", "content": request_data.text}
    # Собираем промпт из трёх частей: системного, в которой подставляем параметры, истории и юзеровского
    messages = [system_message] + [message.dict() for message in request_data.context.history] + [user_message]
    try:
        data = {
            "model": "meta-llama/llama-3.1-8b-instruct",
            "messages": messages,
            "temperature": 0.7
        }

        if not URL:
            raise ValueError("URL route is not set in .env")

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
async def root():
    if api_key and URL:
        return {"message": "Business Assistant API is running", "status": "ok"}
    return {"message": "Business Assistant API key or URL not set", "status": "failed"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8095)
