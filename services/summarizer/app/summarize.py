import os
from typing import List
import logging
import requests
from fastapi import HTTPException
from dotenv import load_dotenv
import aiohttp
from aiohttp import ClientTimeout


load_dotenv()

api_key = os.getenv("SUMMARIZER_API_KEY")
URL = os.getenv("OPENROUTER_URL")

if not URL:
    raise ValueError("URL route is not set in .env")



async def summarize_text(data: dict):
    logger = logging.getLogger(__name__)
    
    try:
        text = data.get("text")
        words_count = data.get("words_count")
        words_count_prompt = ""

        if text is None:
            logger.warning("Summarize text called with None text")
            raise HTTPException(status_code=400, detail="Invalid text field given")

        if not text.strip():
            logger.warning("Summarize text called with empty text")
            raise HTTPException(status_code=400, detail="Empty text given")
        
        logger.info(f"Starting text summarization, text length: {len(text)}, words_count: {words_count}")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://your-app.com",
            "X-Title": "chatbot",
        }

        if words_count:
            words_count_prompt = f" Уложись в {words_count} слов."
            logger.debug(f"Words count constraint: {words_count}")
        
        system_message = {
            "role": "system",
            "content": (
                "Ты опытный аналитик. Твоя задача выделить все основные тезисы и важные факты из текста. "
                "Суммаризируй текст и распиши каждый выбранный пункт. "
                "Будь максимально точен и объективен, сохрани все ключевые моменты, исключи воду и повторения."
                + words_count_prompt
            )
        }

        user_message = {
            "role": "user", 
            "content": f"Вот текст для анализа: {text}"
        }

        payload = {
            "model": "meta-llama/llama-3.1-8b-instruct",
            "messages": [system_message, user_message],
            "temperature": 0.7
        }
        
        if not URL:
            logger.error("URL is not set in environment variables")
            raise ValueError("URL route is not set in .env")

        timeout = ClientTimeout(total=600)
        logger.debug(f"Sending request to {URL} with timeout {timeout.total}s")
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(URL, headers=headers, json=payload) as response:
                
                response.raise_for_status()
                response_data = await response.json()
                
                logger.info("Text summarization completed successfully")
                logger.debug(f"API response received, usage: {response_data.get('usage', {})}")
                
                return {
                    "success": True,
                    "response": response_data["choices"][0]["message"]["content"],
                    "usage": response_data.get("usage", {}),
                    "model": response_data.get("model")
                }
                
    except aiohttp.ServerTimeoutError:
        logger.error("API request timeout exceeded")
        raise HTTPException(status_code=504, detail="External API timeout")
        
    except aiohttp.ServerDisconnectedError:
        logger.error("API server disconnected during request")
        raise HTTPException(status_code=502, detail="External API disconnected")
        
    except KeyError as e:
        logger.error(f"Invalid API response format: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail="Invalid API response format")
        
    except aiohttp.ClientError as e:
        logger.error(f"API request failed: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"External API error: {str(e)}")
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error in summarize_text: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


async def summarize_dialog(data: dict):
    try:
        text = data.get("text", "")
        context = data.get("context")
        business = data.get("business", "Малый бизнес")
        description = data.get("description", "")
        words_count = data.get("words_count")
        if text is None:
            raise HTTPException(status_code=400, detail="Invalid text field given")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://your-app.com",
            "X-Title": "chatbot",
        }
        words_count_prompt = f" Уложись в {words_count} слов." if words_count else ""
        description_prompt = f" Описание бизнеса: {description}" if description else ""
        system_message = {
            "role": "system",
            "content": (
                f"Ты опытный аналитик. Ты получишь историю общения бизнес-ассистента с клиентом-владельцем {business}."
                f"{description_prompt}"
                f" Твоя задача выделить все основные тезисы и важные факты из диалога чтобы их можно было передать в другую модель. "
                f"Суммаризируй текст и распиши каждый выбранный пункт. "
                f"Будь максимально точен и объективен, сохрани все ключевые моменты, исключи воду и повторения."
                f"{words_count_prompt}"
                "Тебе надо упомянуть"
                "1. Основная проблема/вопрос клиента"
                "2. Ключевые рекомендации ассистента"  
                "3. Конкретные действия или решения"
                "4. Важные цифры, сроки, условия"
                "Требования:"
                "- НЕ пересказывай диалог"
                "- НЕ цитируй участников"
                "- Выдели только суть"
                "- Формат: четкие пункты"
                "- Используй только информацию из диалога"
            )
        }
        messages = [system_message]
        if context and isinstance(context, list):
            messages.extend(context)
        user_message = {
            "role": "user", 
            "content": f"Вот диалог для анализа: {text}"
        }
        messages.append(user_message)
        request_data = {
            "model": "meta-llama/llama-3.1-8b-instruct",
            "messages": messages,
            "temperature": 0.7
        }
        if not URL:
            raise HTTPException(status_code=500, detail="URL route is not set in .env")
        resp = requests.post(URL, headers=headers, json=request_data)
        resp.raise_for_status()
        response_data = resp.json()
        if "choices" not in response_data or not response_data["choices"]:
            raise HTTPException(status_code=502, detail="Invalid API response format")
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
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected error in summarize_dialog: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")