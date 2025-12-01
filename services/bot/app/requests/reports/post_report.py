import aiohttp
import os
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def post_report(
    telegram_id: int,
    name: str,
    description: str,
    apc: float,
    avp: float,
    cogs: float,
    cogs1s: float,
    customers: int,
    fc: float,
    tms: float,
    users: int,
    rr: float = 0.2,
    agr: float = 0.1,
) -> dict|None:
    """
    Создает отчет с переданными параметрами
    
    Args:
        telegram_id: ID пользователя в Telegram
        name: Название отчета
        description: Описание отчета
        agr: Average Growth Rate (средний темп роста)
        apc: Average Purchase Cost (средняя стоимость покупки)
        avp: Average Value per User (средняя ценность пользователя)
        cogs: Cost of Goods Sold (себестоимость проданных товаров)
        cogs1s: COGS для первого сценария
        customers: Количество клиентов
        fc: Fixed Costs (постоянные затраты)
        rr: Retention Rate (коэффициент удержания)
        tms: Total Market Share (доля рынка)
        user_id: ID пользователя в системе
        users: Количество пользователей
    """
    load_dotenv()
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
        
    request_url = base_url + "reports"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            request_url,
            json={
                "agr": agr,
                "apc": apc,
                "avp": avp,
                "cogs": cogs,
                "cogs1s": cogs1s,
                "customers": customers,
                "fc": fc,
                "name": name,
                "rr": rr,
                "tms": tms,
                "users": users
            },
            headers={
                "X-Bot-Key": BOT_API_KEY,
                "X-User-ID": str(telegram_id),
                "Content-Type": "application/json" 
            },
        ) as response:
            if response.status in (200, 201, 202, 203, 204, 205):
                data = await response.json()
                logging.info("✅ Отчет успешно создан!")
                return data
            elif response.status == 404:
                logging.error("❌ Route was not found")
                return {
                    "error": "Route was not found",
                    "status": 404
                }
            else:
                logging.error(f"❌ Ошибка: {response.status}")
                return None

# Примеры использования:
# 1. Минимальный вызов
# await post_report(telegram_id=123, name="Отчет 1", description="Тестовый отчет")

# 2. Полный вызов
# await post_report(
#     telegram_id=123,
#     name="Квартальный отчет",
#     description="Анализ продаж за Q1",
#     agr=15.5,
#     apc=1200.0,
#     customers=1500,
#     fc=50000.0,
#     users=2000
# )