import aiohttp
import asyncio
import os
import logging
from dotenv import load_dotenv
from pprint import pprint
from typing import Any, List

async def get_business(telegram_id, business_id = None)->Any | dict[str, Any] | None | List[dict[str, Any]]:
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
    if business_id:
        request_url = base_url+f"businesses/{business_id}/"
    else:
        request_url = base_url+"businesses/"
    logging.info(f"Sending to {request_url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(
            base_url+request_url, 
            headers={
                "X-Bot-Key":f"{BOT_API_KEY}",
                "Content-Type": "application/json",
                "X-User-ID":f"{telegram_id}"
            },
        ) as response:
            if response.status in (200, 201, 202, 203, 204, 205):
                data = await response.json()
                logging.info("Данные успешно получены!")
                return data
            elif response.status == 404:
                logging.error("Business was not found")
                return {
                    "error": "Business was not found",
                    "status": 404
                }
            else:
                logging.error(f"Ошибка: {response.status}")
                return None



async def get_user_business(telegram_id, **kwargs)->Any | dict[str, Any] | None | List[dict[str, Any]]:
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
    request_url = f"users/tg/{telegram_id}"
    logging.info(f"Sending to {request_url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(
            base_url+request_url, 
            headers={
                "X-Bot-Key":f"{BOT_API_KEY}",
                "Content-Type": "application/json",
                "X-User-ID":f"{telegram_id}"
            },
        ) as response:
            if response.status in (200, 201, 202, 203, 204, 205):
                data = await response.json()
                logging.info("Данные успешно получены!")
                return data.get("businesses")
            elif response.status == 404:
                logging.error("Business was not found")
                return {
                    "error": "Business was not found",
                    "status": 404
                }
            else:
                logging.error(f"Ошибка: {response.status}")
                return None



