import aiohttp
import asyncio
import os
import logging
from pprint import pprint
from dotenv import load_dotenv


async def get_text_report(telegram_id):
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
        async with session.get(base_url+"analitics/stats/", headers=headers) as response:
            if response.status == 200 or response.status == 201:
                if "application/json" in response.headers.get("Content-Type", ""):
                    data = await response.json()
                    logging.info("Данные успешно получены!")
                    return data
                else:
                    logging.error(f"API вернул не-JSON ответ. Content-Type: {response.headers.get('Content-Type')}. Тело ответа: {await response.text()}")
                    return None
            else:
                logging.error(f"Ошибка: {response.status}")
                return None


async def main():
    response_data = await get_text_report(telegram_id="6911237041")
    if response_data:
        print("\n--- Результат ---")
        pprint(response_data)

if __name__ == "__main__":
    asyncio.run(main())