import os
from typing import List
import logging
import requests
from fastapi import HTTPException
from dotenv import load_dotenv
from fastapi.responses import JSONResponse

load_dotenv()

api_key = os.getenv("CHAT_MODEL_API_KEY")

URL = os.getenv("OPENROUTER_URL")
if not URL:
    raise ValueError("URL route is not set in .env")
if not api_key:
    raise ValueError("API key is not set in .env")


def generate_recomendation(summary, words_count = None):
    try:
        words_count_prompt = ""
        if summary is None:
            raise HTTPException(status_code=400, detail="Invalid context field given")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://your-app.com",
            "X-Title": "chatbot",
        }
        if words_count:
            words_count_prompt = f"Уложись в {words_count} слов."
        system_message = {
            "role": "system",
            "content": """
        Ты опытный бизнес-аналитик. Проанализируй суммаризацию диалога с владельцем бизнеса.

        ЗАДАЧА:
        Выдели конкретные бизнес-идеи, инициативы и рекомендации по развитию.

        ТРЕБОВАНИЯ:
        - Используй только информацию из суммаризации
        - Не придумывай информацию которой нет в исходных данных  
        - Действуй в рамках законодательства РФ
        - Будь объективен и критически оценивай каждую идею
        - Избегай общих фраз, только конкретные предложения
        - Пиши меньше воды
        - Предлагай оригинальные идеи

        ФОРМАТ ОТВЕТА:
        1. ВЫЯВЛЕННЫЕ ПРОБЛЕМЫ:
        - Проблема 1
        - Проблема 2

        2. КЛЮЧЕВЫЕ ИДЕИ И ИНИЦИАТИВЫ:
        - Идея 1 с обоснованием
        - Идея 2 с обоснованием

        3. РЕКОМЕНДАЦИИ К РЕАЛИЗАЦИИ:
        - Рекомендация 1 с конкретными шагами
        - Рекомендация 2 с конкретными шагами
        """ + (words_count_prompt if words_count_prompt else "")
        }
        user_message = {
            "role": "user", 
            "content": f"Дай мне рекомендации или идеи для развития: {str(summary)}"
        }
        data = {
            "model": "meta-llama/llama-3.1-8b-instruct",
            "messages": [system_message, user_message],
            "temperature": 0.7
        }
        if not URL:
            raise ValueError("URL route is not set in .env")
        resp = requests.post(URL, headers=headers, json=data)
        resp.raise_for_status()
        response_data = resp.json()
        return {
            "success": True,
            "response": response_data["choices"][0]["message"]["content"],
            "usage": response_data.get("usage", {}),
            "model": response_data.get("model")
        }
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
        raise HTTPException(status_code=502, detail="External API error")
    except KeyError as e:
        logging.error(f"Invalid API response format: {e}")
        raise HTTPException(status_code=502, detail="Invalid API response")
    except Exception as e:
        logging.error(f"Unexpected error in summarize_text: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")



