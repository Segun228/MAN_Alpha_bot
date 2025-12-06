import os
from typing import List
import logging
import requests
from fastapi import HTTPException
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import aiohttp
import json

from typing import Dict, Any, Optional
from fastapi import HTTPException

load_dotenv()

api_key = os.getenv("RECOMENDATOR_API_KEY")

URL = os.getenv("OPENROUTER_URL")
if not URL:
    raise ValueError("URL route is not set in .env")
if not api_key:
    raise ValueError("API key is not set in .env")

def validate_openrouter_request(messages: List[Dict]) -> List[Dict]:
    """Валидирует сообщения для OpenRouter API"""
    
    validated = []
    
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        if "role" not in msg or "content" not in msg:
            continue
        if msg["role"] not in ["system", "user", "assistant"]:
            msg["role"] = "user"
        if not isinstance(msg["content"], str):
            msg["content"] = str(msg["content"])
        if len(msg["content"]) > 32000:
            msg["content"] = msg["content"][:32000]
        validated.append(msg)
    return validated


async def generate_recomendation(
    context: Any,
    business: Optional[str] = None,
    description: Optional[str] = None,
    words_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Генерирует бизнес-рекомендации через OpenRouter API
    
    Args:
        context: История диалога или контекст
        business: Название бизнеса
        description: Описание бизнеса
        words_count: Ограничение по количеству слов
    
    Returns:
        Словарь с ответом API
    """
    try:
        if not context:
            raise HTTPException(
                status_code=400, 
                detail="Context is required"
            )
        
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="OpenRouter API key not configured"
            )

        openrouter_url = os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions")

        business_info = ""
        if business:
            business_info += f"Бизнес: {business}\n"
        if description:
            business_info += f"Описание: {description}\n"
        
        words_count_prompt = f" Уложись в {words_count} слов." if words_count else ""
        
        system_content = f"""
Ты бизнес-аналитик. Проанализируй диалог с владельцем бизнеса и предложи конкретные идеи для развития.

{business_info}
Требования:
- Используй только информацию из диалога
- Конкретные предложения, без воды
- В рамках законодательства РФ
{words_count_prompt}

Формат ответа:

1. ИДЕИ:
- Идея 1 + краткое обоснование
- Идея 2 + краткое обоснование  
- Идея 3 + краткое обоснование

2. РЕАЛИЗАЦИЯ:
- Шаг 1 (конкретные действия)
- Шаг 2 (конкретные действия) 
- Шаг 3 (конкретные действия)
"""
        
        system_message = {
            "role": "system",
            "content": system_content.strip()
        }
        
        messages = [system_message]
        
        history_messages = []
        
        if isinstance(context, dict):
            if "history" in context and isinstance(context["history"], list):
                history_messages = context["history"]
            elif "messages" in context and isinstance(context["messages"], list):
                history_messages = context["messages"]
        elif isinstance(context, list):
            history_messages = context
        
        valid_messages = []
        for msg in history_messages:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                if msg["role"] in ["user", "assistant", "system"]:
                    if len(str(msg["content"])) > 10000:
                        msg["content"] = str(msg["content"])[:10000] + "..."
                    valid_messages.append(msg)
        messages.extend(valid_messages)
        
        logging.info(f"Total messages: {len(messages)}")
        logging.info(f"System message length: {len(system_content)}")
        
        payload = {
            "model": "meta-llama/llama-3.1-8b-instruct",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000,
            "stream": False
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://your-app.com",
            "X-Title": "Business Analysis Bot",
        }
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                openrouter_url,
                headers=headers,
                json=payload,
                timeout=timeout
            ) as resp:
                if resp.status == 400:
                    error_data = await resp.json()
                    error_detail = error_data.get("error", {}).get("message", "Bad Request")
                    
                    logging.error(f"OpenRouter 400 Error: {error_detail}")
                    logging.error(f"Request payload: {json.dumps(payload, ensure_ascii=False)[:500]}")
                    
                    raise HTTPException(
                        status_code=400,
                        detail=f"OpenRouter validation error: {error_detail}"
                    )
                
                elif resp.status == 401:
                    raise HTTPException(
                        status_code=401,
                        detail="Invalid API key"
                    )
                
                elif resp.status == 429:
                    raise HTTPException(
                        status_code=429,
                        detail="Rate limit exceeded"
                    )
                
                elif resp.status == 500:
                    error_text = await resp.text()
                    logging.error(f"OpenRouter 500 Error: {error_text}")
                    raise HTTPException(
                        status_code=502,
                        detail="OpenRouter internal error"
                    )
                
                elif resp.status != 200:
                    error_text = await resp.text()
                    logging.error(f"OpenRouter Error {resp.status}: {error_text}")
                    raise HTTPException(
                        status_code=502,
                        detail=f"OpenRouter error: {resp.status}"
                    )

                response_data = await resp.json()
                
                if "choices" not in response_data or not response_data["choices"]:
                    raise HTTPException(
                        status_code=502,
                        detail="Invalid response format from OpenRouter"
                    )
                
                return {
                    "success": True,
                    "response": response_data["choices"][0]["message"]["content"],
                    "usage": response_data.get("usage", {}),
                    "model": response_data.get("model"),
                    "id": response_data.get("id")
                }
    
    except aiohttp.ClientError as e:
        logging.error(f"Network error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Network error: {str(e)}"
        )
    
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error: {e}")
        raise HTTPException(
            status_code=502,
            detail="Invalid JSON response"
        )
    
    except Exception as e:
        logging.exception(f"Unexpected error in generate_recomendation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )