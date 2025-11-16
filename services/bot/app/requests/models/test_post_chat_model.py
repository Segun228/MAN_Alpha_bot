import aiohttp
import os
import logging
from dotenv import load_dotenv
import asyncio
from pprint import pprint

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def post_chat_model(
    telegram_id,
    text=None,
    business=None,
    context=None,
    symbol_threshold=20,
    base_url=None
):
    load_dotenv()
    
    if base_url is None:
        base_url = os.getenv("BASE_URL")
    BOT_API_KEY = os.getenv("BOT_API_KEY")
    
    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not BOT_API_KEY:
        logging.error("No BOT_API_KEY was provided")
        raise ValueError("No BOT_API_KEY was provided")
    if not telegram_id:
        logging.error("No telegram_id was provided")
        raise ValueError("No telegram_id was provided")

    if not base_url.endswith('/'):
        base_url += '/'
    
    request_url = base_url + "models/chat"
    

    test_history = [
        {
            "message": "Привет! У меня есть бизнес по продаже органических продуктов. Можете помочь с анализом?",
            "direction": "question",
            "timestamp": "2024-01-15T10:00:00"
        },

        {
            "message": "Мы продаем органические овощи и фрукты напрямую с фермы. Основные клиенты - люди 25-45 лет, заботящиеся о здоровом питании. Продаем через Instagram и сайт.",
            "direction": "question",
            "timestamp": "2024-01-15T10:02:00"
        }
    ]

    filtered_history = []
    for el in test_history:
        if el.get("message") and len(el.get("message")) >= symbol_threshold:
            filtered_history.append({
                "role": "user" if el.get('direction') == "question" else "assistant",
                "content": el.get("message").replace('\n', ' ')
            })

    final_context = filtered_history
    if context:
        if isinstance(context, list):
            final_context.extend(context)
        else:
            final_context.append({"role": "user", "content": str(context)})
    
    logging.info(f"Отправка запроса к {request_url}")
    logging.info(f"Контекст: {len(final_context)} сообщений")
    logging.info(f"Текст: {text}")
    
    async with aiohttp.ClientSession(timeout = aiohttp.ClientTimeout(total=600)) as session:
        pprint({
                "telegram_id": telegram_id,
                "text": text,
                "business": business,
                "context": {"history":final_context}
            })
        async with session.post(
            request_url,
            json={
                "telegram_id": telegram_id,
                "text": text,
                "business": business,
                "context": {"history":final_context}
            },
            headers={
                "X-Bot-Key": BOT_API_KEY,
                "X-User-ID": str(telegram_id),
                "Content-Type": "application/json" 
            },
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if response.status in (200, 201, 202, 203, 204):
                data = await response.json()
                logging.info("✅ Сообщение модели отправлено!")
                return data
            else:
                error_text = await response.text()
                logging.error(f"❌ Ошибка {response.status}: {error_text}")
                return {
                    "error": f"HTTP {response.status}",
                    "details": error_text
                }


if __name__ == "__main__":
    async def test_post_chat_model():
        print("=== ТЕСТИРОВАНИЕ POST_CHAT_MODEL ===")
        
        test_cases = [
            {
                "telegram_id": 6911237041,
                "text": "расскажи про законность майонезного пирога",
                "business": "кофейня",
                "context": {
                    "history": [
                        {"role": "assistant", "content": "дико здравствуйте"},
                        {"role": "user", "content": "хочу кофейню просто пиздец крутую"}
                    ]
                },
                "symbol_threshold": 10,
                "base_url": "http://localhost:8083/"
            },
            {
                "telegram_id": 123456789,
                "text": "напиши для нас пафосный пост в инстаграм про новый капучино",
                "business": "кофейня",
                "context": {
                    "history": [
                        {"role": "user", "content": "Привет, я владелец кофейны 'Без Ума' в Царицыно"},
                        {"role": "assistant", "content": "Приветствую, безумный владелец! Царицыно — это вам не Шарицыно."},
                        {"role": "user", "content": "ахах, точно! наша фишка — бармены с характером и кофе с перцем"}
                    ]
                },
                "symbol_threshold": 5,
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
                import traceback
                traceback.print_exc()

    asyncio.run(test_post_chat_model())