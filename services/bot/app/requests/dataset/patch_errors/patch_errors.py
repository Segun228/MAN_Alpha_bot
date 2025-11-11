import aiohttp
import asyncio
import os
import logging
from dotenv import load_dotenv
from pprint import pprint
from io import BytesIO
from app.kafka.utils import build_log_message

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def patch_errors(telegram_id, dataset_id, alpha = 0.05, beta = 0.2):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id or not dataset_id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }

        exact_url = f"{base_url}api/datasets/{dataset_id}/"
        logging.debug(f"Sending to {exact_url}")

        data = {
            "alpha":alpha,
            "beta":beta
        }
        async with session.patch(
            exact_url,
            headers=headers,
            data=data
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("Датасет изменен")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=str(data)
                )
                return await response.json()
            else:
                text = await response.text()
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = text
                )
                logging.error(f"Ошибка {response.status}: {text}")
                return None