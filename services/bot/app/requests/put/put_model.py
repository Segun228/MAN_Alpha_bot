import aiohttp
import asyncio
import os
import logging
from dotenv import load_dotenv
from pprint import pprint
from io import BytesIO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def put_model(
    telegram_id, 
    model_id,  
    name:str|None = "Model", 
    description:str|None="Description", 
):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id or not model_id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }
        data = {
            "name":name,
            "description":description
        }
        exact_url = f"{base_url}ml-algorithms/model/{model_id}/"
        logging.debug(f"Sending to {exact_url}")
        async with session.patch(
            exact_url,
            headers=headers,
            data=data
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("Датасет изменен")
                return await response.json()
            else:
                text = await response.text()
                logging.error(f"Ошибка {response.status}: {text}")
                return None