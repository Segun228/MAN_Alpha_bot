import aiohttp
import os
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def put_report(
    report_id: int,
    telegram_id: int,
    name: str,
    description: str,
    agr: float,
    apc: float,
    avp: float,
    cogs: float,
    cogs1s: float,
    customers: int,
    fc: float,
    rr: float,
    tms: float,
    user_id: int,
    users: int
) -> dict|None:
    """
    Обновляет отчет по ID
    
    Args:
        report_id: ID отчета для обновления
        telegram_id: ID пользователя в Telegram
        name: Название отчета (опционально)
        description: Описание отчета (опционально)
        agr: Average Growth Rate (опционально)
        apc: Average Purchase Cost (опционально)
        avp: Average Value per User (опционально)
        cogs: Cost of Goods Sold (опционально)
        cogs1s: COGS для первого сценария (опционально)
        customers: Количество клиентов (опционально)
        fc: Fixed Costs (опционально)
        rr: Retention Rate (опционально)
        tms: Total Market Share (опционально)
        user_id: ID пользователя в системе (опционально)
        users: Количество пользователей (опционально)
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
    if not report_id:
        logging.error("No report_id was provided")
        raise ValueError("No report_id was provided")
        
    request_url = f"{base_url}reports/{report_id}"
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description
    if agr is not None:
        update_data["agr"] = agr
    if apc is not None:
        update_data["apc"] = apc
    if avp is not None:
        update_data["avp"] = avp
    if cogs is not None:
        update_data["cogs"] = cogs
    if cogs1s is not None:
        update_data["cogs1s"] = cogs1s
    if customers is not None:
        update_data["customers"] = customers
    if fc is not None:
        update_data["fc"] = fc
    if rr is not None:
        update_data["rr"] = rr
    if tms is not None:
        update_data["tms"] = tms
    if user_id is not None:
        update_data["user_id"] = user_id
    if users is not None:
        update_data["users"] = users
    async with aiohttp.ClientSession() as session:
        async with session.put(
            request_url,
            json=update_data,
            headers={
                "X-Bot-Key": BOT_API_KEY,
                "X-User-ID": str(telegram_id),
                "Content-Type": "application/json" 
            },
        ) as response:
            if response.status in (200, 201, 202, 203, 204):
                data = await response.json()
                logging.info(f"✅ Отчет {report_id} успешно обновлен!")
                return data
            elif response.status == 404:
                logging.error(f"❌ Отчет {report_id} не найден")
                return {
                    "error": "Report not found",
                    "status": 404
                }
            else:
                logging.error(f"❌ Ошибка при обновлении отчета {report_id}: {response.status}")
                return None