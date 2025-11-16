import aiohttp
import asyncio
import os
import logging
from dotenv import load_dotenv
from pprint import pprint

async def get_admin_ids(telegram_id):
    load_dotenv()
    base_url = os.getenv("BASE_URL")
    BOT_API_KEY = os.getenv("BOT_API_KEY")
    if not base_url or base_url is None:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not BOT_API_KEY or BOT_API_KEY is None:
        logging.error("No BOT_API_KEY was provided")
        raise ValueError("No BOT_API_KEY was provided")
    if not telegram_id or telegram_id is None:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            base_url+"users", 
            headers={
                "X-Bot-Key":f"{BOT_API_KEY}",
                "X-User-ID":f"{telegram_id}"
            }
        ) as response:
            if response.status in (200, 201, 202, 203, 204, 205):
                data = await response.json()
                logging.info("Данные успешно получены!")
                logging.info(str(data))
                result = []
                for el in data:
                    if isinstance(el, dict) and el.get("is_admin"):
                        if el.get("telegram_id") is not None:
                            result.append(el.get("telegram_id"))
                admin_id = os.getenv("ADMINS")
                if not admin_id:
                    return result
                admin_id = list(map(int, admin_id.split("_")))
                if len(admin_id) >= 1:
                    result.extend(admin_id)
                return result
            elif response.status == 404:
                logging.error("The route is not found")
                return {
                    "error": "The route is not found",
                    "status": 404
                }
            else:
                logging.error(f"Ошибка: {response.status}")
                return None


async def main():
    response_data = await get_admin_ids(telegram_id="6911237041")
    if response_data:
        print("\n--- Результат ---")
        pprint(response_data)
    else:
        print("\n--- Ощибка ---")
        pprint(response_data)

if __name__ == "__main__":
    asyncio.run(main())