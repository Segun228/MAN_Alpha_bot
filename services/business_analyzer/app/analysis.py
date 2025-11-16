import os
from typing import List
import logging
import requests
from fastapi import HTTPException
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from typing import Literal
from app.prompts import PROMPTS
import aiohttp


load_dotenv()

api_key = os.getenv("ANALYSER_API_KEY")

URL = os.getenv("OPENROUTER_URL")
if not URL:
    raise ValueError("URL route is not set in .env")
if not api_key:
    raise ValueError("API key is not set in .env")



async def generate_analysis(
    context,
    business,
    analysis_type: Literal["swot", "cjm", "bmc", "vpc", "pest"],
    description=None,
    words_count=None,
):
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
        business_info = f"Бизнес: {business}"
        if description:
            business_info += f"\nОписание: {description}"

        system_message = {
            "role": "system",
            "content": f"{business_info}\n\n{PROMPTS[analysis_type]}{words_count_prompt}"
        }
        
        messages = [system_message]
        
        history_messages = []
        
        if isinstance(context, dict) and context.get("history"):
            history_messages = context["history"]
        elif isinstance(context, list):
            history_messages = context
        
        if not history_messages:
            user_message = {
                "role": "user",
                "content": "Проанализируй предоставленную информацию о бизнесе"
            }
            messages.append(user_message)
        else:
            valid_messages = [
                msg for msg in history_messages 
                if msg.get("content") and msg.get("role") in ["user", "assistant"]
            ]
            messages.extend(valid_messages)
            
            if len(messages) == 1:
                user_message = {
                    "role": "user", 
                    "content": "Проанализируй предоставленную информацию о бизнесе"
                }
                messages.append(user_message)

        payload = {
            "model": "meta-llama/llama-3.1-8b-instruct",
            "messages": messages,
            "temperature": 0.8,
            "max_tokens": 3000,
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.3,
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
        logging.error(f"Unexpected error in generate_analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")