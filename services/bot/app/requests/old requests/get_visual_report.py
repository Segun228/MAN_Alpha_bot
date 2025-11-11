import aiohttp
import asyncio
import os
import logging
from pprint import pprint
from dotenv import load_dotenv
import io
import zipfile
from typing import List, Dict, Any, Union

async def get_visual_report(telegram_id) -> Union[List[bytes], None]:
    load_dotenv()
    base_url = os.getenv("BASE_URL")
    if not base_url or base_url is None:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id or telegram_id is None:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }
        async with session.get(base_url+"analitics/visual/", headers=headers) as response:
            if response.status == 200 or response.status == 201:
                zip_bytes = await response.read()
                logging.info("Данные успешно получены!")
                zip_buffer = io.BytesIO(zip_bytes)
                image_bytes_list = []
                with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
                    for filename in zip_file.namelist():
                        if filename.endswith('.png'):
                            image_bytes = zip_file.read(filename)
                            image_bytes_list.append(image_bytes)
                return image_bytes_list
            else:
                logging.error(f"Ошибка: {response.status}")
                return None


async def main():
    response_data = await get_visual_report(telegram_id="6911237041")
    if response_data:
        print("\n--- Результат ---")


if __name__ == "__main__":
    asyncio.run(main())