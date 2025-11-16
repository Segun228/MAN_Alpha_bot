import aiohttp
import os
import logging
from dotenv import load_dotenv
from io import BytesIO
import asyncio
from pprint import pprint
# from app.requests.models.get_messages import get_messages
from .get_messages import get_messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def post_chat_model(
    telegram_id,
    text=None,
    description=None,
    business=None,
    context=None,
    symbol_threshold = 20,
    base_url = None
):
    load_dotenv()
    if base_url is None or not base_url:
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
    # request_url = base_url + "models/chat"
    request_url = "http://chat-model:8082/generate_response"
    history = (await get_messages(
        telegram_id=telegram_id
    ))
    if not history:
        raise ValueError("Could not get history from the server")
    history = history.get("data")
    result = []
    for el in history:
        if not el.get("message") or len(el.get("message")) < symbol_threshold:
            continue
        result.append(
            {
                "role":("user" if el.get('direction') == "question" else "assistant"),
                "content":el.get("message").replace('\n', ' ')
            }
        )
    async with aiohttp.ClientSession(timeout = aiohttp.ClientTimeout(total=600)) as session:
        async with session.post(
            request_url,
            json={
                "telegram_id":telegram_id,
                "text":text,
                "business":business,
                "context": {'history':result},
                "description": description
            },
            headers={
                "X-Bot-Key":f"{BOT_API_KEY}",
                "X-User-ID":f"{telegram_id}",
                "Content-Type": "application/json" 
            },
        ) as response:
            if response.status in (200, 201, 202, 203, 204, 205):
                data = await response.json()
                logging.info("Сообщение модели отправлено!")
                if hasattr(data, "get"):
                    return data.get("response")
                return data
            elif response.status == 404:
                logging.error("Route was not found")
                return {
                    "error": "Route was not found",
                    "status": 404
                }
            else:
                logging.error(f"Ошибка: {response.status}")
                return None


if __name__ == "__main__":
    async def test_post_chat_model():
        print("=== ТЕСТИРОВАНИЕ POST_CHAT_MODEL ===")
        
        # Тестовые данные
        test_cases = [
            {
                "telegram_id": 6911237041,
                "text": "Привет! Помоги мне проанализировать мой бизнес",
                "business": "Консультации по маркетингу",
                "context": None,
                "symbol_threshold": 10,
                "base_url": "http://localhost:8083/"
            },
            {
                "telegram_id": 123456789, 
                "text": "Какие рекомендации вы можете дать?",
                "business": None,
                "context": "Дополнительный контекст",
                "symbol_threshold": 20,
                "base_url": "http://localhost:8083/"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Тест {i} ---")
            print(f"Параметры: {test_case}")
            
            try:
                result = await post_chat_model(**test_case)
                print("✅ РЕЗУЛЬТАТ:")
                pprint(result)
                
            except Exception as e:
                print(f"❌ ОШИБКА: {e}")
                logging.exception("Детали ошибки:")

    asyncio.run(test_post_chat_model())