import aiohttp
import asyncio
import os
import logging
from dotenv import load_dotenv
from pprint import pprint

async def make_admin(telegram_id, target_user_id, value=True):
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
        async with session.patch(
            base_url+f"auth/user/{target_user_id}/", 
            headers = headers,
            json={"is_staff": value}
        ) as response:
            if response.status in (200, 201, 202, 203, 204):
                data = await response.json()
                logging.info("Данные успешно отправлены!")
                return data
            else:
                logging.error(f"Ошибка: {response.status}")
                return None


async def main():
    response_data = await make_admin(telegram_id="6911237041",target_user_id=21231, value= True)
    if response_data:
        print("\n--- Результат ---")
        pprint(response_data)

if __name__ == "__main__":
    asyncio.run(main())