import os
from typing import List
import logging
import requests
from fastapi import HTTPException
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import aiohttp

load_dotenv()

api_key = os.getenv("RECOMENDATOR_API_KEY")

URL = os.getenv("OPENROUTER_URL")
if not URL:
    raise ValueError("URL route is not set in .env")
if not api_key:
    raise ValueError("API key is not set in .env")



async def generate_recomendation(context, business, description, words_count=None):
    try:
        if not context:
            raise HTTPException(status_code=400, detail="Invalid context provided")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://your-app.com",
            "X-Title": "chatbot",
        }

        words_count_prompt = f" Уложись в {words_count} слов." if words_count else ""

        system_message = {
            "role": "system",
            "content": f"""
Ты бизнес-аналитик. Проанализируй диалог с владельцем бизнеса и предложи конкретные идеи для развития.

{business} {description}

Требования:
- Используй только информацию из диалога
- Конкретные предложения, без воды
- В рамках законодательства РФ
{words_count_prompt}

Формат:

1. ИДЕИ:
- Идея 1 + обоснование
- Идея 2 + обоснование  
- Идея 3 + обоснование

2. РЕАЛИЗАЦИЯ:
- Шаг 1 (конкретные действия)
- Шаг 2 (конкретные действия)
- Шаг 3 (конкретные действия)
"""
        }

        messages = [system_message]
        
        if context.get("history"):
            messages.extend(context["history"])
        else:
            messages.extend(context)

        payload = {
            "model": "meta-llama/llama-3.1-8b-instruct",
            "messages": messages,
            "temperature": 0.7
        }

        if not URL:
            raise ValueError("URL route is not set in .env")

        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(URL, headers=headers, json=payload) as resp:
                resp.raise_for_status()
                response_data = await resp.json()

                return {
                    "success": True,
                    "response": response_data["choices"][0]["message"]["content"],
                    "usage": response_data.get("usage", {}),
                    "model": response_data.get("model")
                }

    except aiohttp.ClientError as e:
        logging.error(f"API request failed: {e}")
        raise HTTPException(status_code=502, detail="External API error")
    except KeyError as e:
        logging.error(f"Invalid API response format: {e}")
        raise HTTPException(status_code=502, detail="Invalid API response format")
    except Exception as e:
        logging.error(f"Unexpected error in generate_recomendation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")