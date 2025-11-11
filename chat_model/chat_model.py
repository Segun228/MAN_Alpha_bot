import os
from typing import List

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

api_key = "ВЫНЕСТИ В .ENV, пока просите у меня лично"
API_KEY = os.environ.get("OPENROUTER_API_KEY")
app = FastAPI()
url = "https://openrouter.ai/api/v1/chat/completions"


class Message(BaseModel):
    role: str  # "user" или "assistant"
    content: str


class Context(BaseModel):
    history: List[Message] = []


class RequestData(BaseModel):
    text: str
    context: Context
    business: str = "малый бизнес"
    description: str = ""


@app.post("/generate_response")
def generate_message(request_data: RequestData):
    if not request_data.text.strip():
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
        "X-Title": "chatbot",
    }

    business_description = ""
    if request_data.description:
        business_description = "Более подробное описание бизнеса: " + request_data.description

    system_message = {
        "role": "system",
        "content": f"Ты опытный бизнес-ассистент. Твоя задача дать точную консультауию для владельца {request_data.business}. "
                   f"{business_description}. Опирайся на существующий опыт и правила, не давай вредных и опасных советов. "
                   f"Не нарушай законодательство РФ и международные нормы. Упомянай, что информацию необходимо "
                   f"проверять самостоятельно."
    }
    user_message = {"role": "user", "content": request_data.text}
    messages = [system_message] + [message.dict() for message in request_data.context.history] + [user_message]
    try:
        data = {
            "model": "meta-llama/llama-3.1-8b-instruct",
            "messages": messages,
            "temperature": 0.7
        }
        resp = requests.post(url, headers=headers, json=data)
        resp.raise_for_status()
        response_data = resp.json()
        return {
            "success": True,
            "response": response_data["choices"][0]["message"]["content"],
            "usage": response_data.get("usage", {}),
            "model": response_data.get("model")
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при запросе к OpenRouter: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Неожиданная ошибка: {str(e)}")


@app.get("/model_health")
def root():
    return {"message": "Business Assistant API is running", "status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
