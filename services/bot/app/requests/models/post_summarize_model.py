import aiohttp
import os
import logging
from dotenv import load_dotenv
from io import BytesIO
import asyncio
from pprint import pprint
# from app.requests.models.get_messages import get_messages
from .get_messages import get_messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def post_summarize_model(
    telegram_id,
    text=None,
    symbol_threshold = 20,
    base_url = None
):
    load_dotenv()
    if base_url is None or not base_url:
        base_url = os.getenv("BASE_URL")
    BOT_API_KEY = os.getenv("BOT_API_KEY")
    if not base_url or base_url is None:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not BOT_API_KEY or BOT_API_KEY is None:
        logging.error("No BOT_API_KEY was provided")
        raise ValueError("No BOT_API_KEY was provided")
    if not telegram_id or telegram_id is None:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    # request_url = base_url + "models/summarize/text"
    request_url = "http://summarizer:8086/summarize/text"
    async with aiohttp.ClientSession(timeout = aiohttp.ClientTimeout(total=600)) as session:
        async with session.post(
            request_url,
            json={
                "telegram_id":telegram_id,
                "text":text,
            },
            headers={
                "X-Bot-Key":f"{BOT_API_KEY}",
                "X-User-ID":f"{telegram_id}",
                "Content-Type": "application/json" 
            },
        ) as response:
            if response.status in (200, 201, 202, 203, 204, 205):
                data = await response.json()
                logging.info("Сообщение модели отправлено!")
                return data
            elif response.status == 404:
                logging.error("Route was not found")
                return {
                    "error": "Route was not found",
                    "status": 404
                }
            else:
                logging.error(f"Ошибка: {response.status}")
                return None

