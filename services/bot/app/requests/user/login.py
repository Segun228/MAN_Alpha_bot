import aiohttp
import asyncio
import os
import logging
from dotenv import load_dotenv


async def login(telegram_id):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url or base_url is None:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id or telegram_id is None:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            base_url+"auth/user/", 
            data={
                "telegram_id": telegram_id, 
                "is_alive":True
            }, 
            headers={"Authorization":f"Bot {telegram_id}"}
        ) as response:
            if response.status == 200 or response.status == 201:
                data = await response.json()
                logging.info("Данные успешно получены!")
                return data
            else:
                logging.error(f"Ошибка: {response.status}")
                return None


async def main():
    response_data = await login(telegram_id="6911237041")
    if response_data:
        print("\n--- Результат ---")
        print(response_data)

if __name__ == "__main__":
    asyncio.run(main())