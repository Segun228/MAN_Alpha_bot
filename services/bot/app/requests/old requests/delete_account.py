import aiohttp
import asyncio
import os
import logging
from dotenv import load_dotenv
from app.kafka.utils import build_log_message
# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def delete_account(telegram_id):
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
        exact_url = f"{base_url}users/user/{telegram_id}/" 
        logging.info(f"Sending to {exact_url}")
        
        async with session.delete(
            exact_url, 
            headers=headers
        ) as response:
            if response.status == 204:
                logging.info(f"Пользователь с ID {telegram_id} успешно удален!")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=str(exact_url)
                )
                return True
            else:
                error_text = await response.text()
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=str(exact_url)
                )
                logging.error(f"Ошибка: {response.status}, Ответ: {error_text}")
                return None


async def main():
    try:
        delete_id = int(input("Введите ID пользователя для удаления: "))
        response_data = await delete_account(telegram_id=delete_id)
        if response_data:
            print(f"Аккаунт {delete_id} успешно удалён.")
        else:
            print(f"Не удалось удалить аккаунт {delete_id}.")
    except ValueError:
        print("Пожалуйста, введите корректный числовой ID.")


if __name__ == "__main__":
    asyncio.run(main())