import aiohttp
import asyncio
import os
import logging
from dotenv import load_dotenv
from pprint import pprint
from io import BytesIO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def post_dataset(telegram_id, name, description="", csv_buffer:(BytesIO|None) = None):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    if csv_buffer is None:
        raise ValueError("CSV buffer is empty")

    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }

        exact_url = f"{base_url}api/datasets/"
        logging.debug(f"Sending to {exact_url}")

        form = aiohttp.FormData()
        form.add_field("name", name)
        form.add_field("description", description)

        csv_buffer.seek(0)
        form.add_field(
            "file",
            csv_buffer,
            filename=f"{name}.csv",
            content_type="text/csv"
        )

        async with session.post(
            exact_url,
            headers=headers,
            data=form
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("Датасет отправлен")
                return await response.json()
            else:
                text = await response.text()
                logging.error(f"Ошибка {response.status}: {text}")
                return None