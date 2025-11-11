import aiohttp
import asyncio
import os
import logging
from dotenv import load_dotenv
from pprint import pprint
from app.kafka.utils import build_log_message

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

async def get_datasets(telegram_id):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
        
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }
        exact_url = f"{base_url}api/datasets/" 
        logging.debug(f"Sending to {exact_url}")
        
        async with session.get(
            exact_url, 
            headers=headers
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("датасеты получены")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=str(response.json())
                )
                return await response.json()
            else:
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = response.json()
                )
                return None

async def get_dataset_file(telegram_id, url):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")

    CLOUD_API_KEY = os.getenv("CLOUD_API_KEY")

    if not CLOUD_API_KEY:
        logging.exception("Missing env required fields")
        raise ValueError("Missing env required fields")
    async with aiohttp.ClientSession() as session:
        response = await session.get(
                url=url,
                headers={
                    "Authorization": f"Bearer {CLOUD_API_KEY}",
                    "Content-Type": "text/csv"
                }
            )
        if response.status in (200, 201, 202, 203):
            logging.info("файл датасета получены")
            await build_log_message(
                telegram_id=telegram_id,
                action="request",
                platform="bot",
                is_authenticated=True,
                source="aiohttp",
                level="INFO",
                payload=str(response.json())
            )
            return await response.read()
        else:
            body = await response.text()
            logging.error(
                "Ошибка при загрузке датасета: статус=%s, причина=%s, тело ответа=%s",
                response.status,
                response.reason,
                url,
                body
            )
            await build_log_message(
                telegram_id=telegram_id,
                action="request",
                platform="bot",
                is_authenticated=True,
                source="aiohttp error handler",
                level="ERROR",
                payload = body
            )
            return None

async def retrieve_dataset(telegram_id, dataset_id):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
        
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }
        exact_url = f"{base_url}api/datasets/{dataset_id}/" 
        logging.debug(f"Sending to {exact_url}")
        
        async with session.get(
            exact_url, 
            headers=headers
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("датасет получен")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=str(response.json())
                )
                return await response.json()
            else:
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = response.text
                )
                return None

async def main():
    try:
        delete_id = int(input("Введите ID пользователя: "))
        response_data = await get_datasets(telegram_id=delete_id)
        pprint(response_data)
    except ValueError:
        print("Пожалуйста, введите корректный числовой ID.")


if __name__ == "__main__":
    asyncio.run(main())