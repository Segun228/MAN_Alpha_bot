import aiohttp
import asyncio
import os
import logging
from dotenv import load_dotenv
from pprint import pprint
from app.kafka.utils import build_log_message
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def delete_dataset(telegram_id, dataset_id):
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
        async with session.delete(
            exact_url, 
            headers=headers,
        ) as response:
            if response.status in (200, 201, 202, 203, 204):
                logging.info("датасет удален")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=exact_url
                )
                return True
            else:
                error_text = await response.text()
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = error_text
                )
                logging.error(f"Failed to delete dataset: {response.status} - {error_text}")
                return None


async def main():
    try:
        response_data = await delete_dataset(telegram_id=6911237041, dataset_id=4)
        pprint(response_data)
    except ValueError:
        print("Пожалуйста, введите корректный числовой ID.")


if __name__ == "__main__":
    asyncio.run(main())