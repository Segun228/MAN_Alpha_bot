import aiohttp
import asyncio
import os
import logging
from dotenv import load_dotenv
from pprint import pprint

async def get_last_expense(telegram_id):
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
        async with session.get(
            base_url+"api/expenses/",
            headers = headers,
        ) as response:
            if response.status == 200 or response.status == 201:
                data = await response.json()
                logging.info("Данные успешно отправлены!")
                return data[-1]
            else:
                logging.error(f"Ошибка: {response.status}")
                return None

async def main():
    response_data = await get_last_expense(telegram_id="6911237041")
    if response_data:
        print("\n--- Результат ---")
        pprint(response_data)
    else:
        print("\n--- Ошибка при получении данных ---")

if __name__ == "__main__":
    asyncio.run(main())