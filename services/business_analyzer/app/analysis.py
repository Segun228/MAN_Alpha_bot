import os
from typing import List
import logging
import requests
from fastapi import HTTPException
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from typing import Literal
from app.prompts import PROMPTS

load_dotenv()

api_key = os.getenv("ANALYSER_API_KEY")

URL = os.getenv("OPENROUTER_URL")
if not URL:
    raise ValueError("URL route is not set in .env")
if not api_key:
    raise ValueError("API key is not set in .env")


def generate_analysis(
    summary, 
    type:Literal["swot", "cjm", "bmc", "vpc", "pest"],
    words_count = None,
):
    """
        SWOT - Strengths Weaknesses Opportunities Threats
        CJM - Customer Journey Map
        BMC - Business Model Canvas
        VPC - value proposition canvas
    """
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
            "content": PROMPTS[type] + (words_count_prompt if words_count_prompt else "")
        }
        user_message = {
            "role": "user", 
            "content": f"Вот краткое содержание нашего диалога: {str(summary)}"
        }
        data = {
            "model": "meta-llama/llama-3.1-8b-instruct",
            "messages": [system_message, user_message],
            "temperature": 0.8,
            "max_tokens": 3000,
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.3, 
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
        



