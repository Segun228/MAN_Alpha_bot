import aiohttp
import os
import logging
from dotenv import load_dotenv
from io import BytesIO
from
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def post_business(
    telegram_id,
    name,
    description,
):
    load_dotenv()
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
    request_url = base_url + f"users/tg/{telegram_id}/businesses"
    async with aiohttp.ClientSession() as session:
        async with session.post(
            request_url,
            json={
                "telegram_id":telegram_id,
                "name":name,
                "description":description,
            },
            headers={
                "X-Bot-Key":f"{BOT_API_KEY}",
                "X-User-ID":f"{telegram_id}",
                "Content-Type": "application/json" 
            },
        ) as response:
            if response.status in (200, 201, 202, 203, 204, 205):
                data = await response.json()
                logging.info("Бизнес успешно создан!")
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