import aiohttp
import asyncio
import os
import logging
from dotenv import load_dotenv
from pprint import pprint

async def post_expense(telegram_id, user_category, user_value, user_title):
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
        async with session.post(
            base_url+"api/expenses/", 
            headers = headers,
            data={
                "title": user_title,
                "value": user_value,
                "category": user_category
            }
        ) as response:
            if response.status == 200 or response.status == 201:
                data = await response.json()
                logging.info("Данные успешно отправлены!")
                return data
            else:
                logging.error(f"Ошибка: {response.status}")
                return None


async def main():
    response_data = await post_expense(telegram_id="6911237041", user_category="other", user_value=550, user_title="Поход в магазин")
    if response_data:
        print("\n--- Результат ---")
        pprint(response_data)
    else:
        print("\n--- Ошибка при отправке данных ---")

if __name__ == "__main__":
    asyncio.run(main())