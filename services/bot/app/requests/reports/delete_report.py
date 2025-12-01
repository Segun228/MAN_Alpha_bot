import aiohttp
import os
import logging
from dotenv import load_dotenv


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def delete_report(
    report_id: int,
    telegram_id: int
) -> dict|None:
    """
    Удаляет отчет по ID
    
    Args:
        report_id: ID отчета для удаления
        telegram_id: ID пользователя в Telegram
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
    
    async with aiohttp.ClientSession() as session:
        async with session.delete(
            request_url,
            headers={
                "X-Bot-Key": BOT_API_KEY,
                "X-User-ID": str(telegram_id),
                "Content-Type": "application/json" 
            },
        ) as response:
            if response.status in (200, 202, 204):
                logging.info(f"✅ Отчет {report_id} успешно удален!")
                return {"status": "success", "message": "Report deleted"}
            elif response.status == 404:
                logging.error(f"❌ Отчет {report_id} не найден")
                return {
                    "error": "Report not found",
                    "status": 404
                }
            else:
                logging.error(f"❌ Ошибка при удалении отчета {report_id}: {response.status}")
                return None