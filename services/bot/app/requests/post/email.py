import aiohttp
import os
import logging
from dotenv import load_dotenv
import io

async def send_zip_email_with_auth(
    zip_buffer: io.BytesIO,
    receiver_email: str,
    telegram_id: str,
    subject: str = "Отчет по анализу",
    text_message: str = "Прикреплен архив с отчетом",
    filename: str = "report.zip"
):
    """
    Отправляет ZIP архив на email с авторизацией через заголовки
    
    Args:
        zip_buffer: BytesIO буфер с ZIP архивом
        receiver_email: Email получателя
        telegram_id: Telegram ID пользователя (для авторизации)
        subject: Тема письма
        text_message: Текст письма
        filename: Имя файла для отправки
        
    Returns:
        dict: Результат отправки
    """
    load_dotenv()
    # base_url = os.getenv("BASE_URL")
    base_url = "http://email_service:8094/"
    BOT_API_KEY = os.getenv("BOT_API_KEY")
    
    if not base_url or base_url is None:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    
    if not BOT_API_KEY or BOT_API_KEY is None:
        logging.error("No BOT_API_KEY was provided")
        raise ValueError("No BOT_API_KEY was provided")
    
    if not receiver_email or receiver_email is None:
        logging.error("No receiver_email was provided")
        raise ValueError("No receiver_email was provided")
    
    if not telegram_id or telegram_id is None:
        logging.error("No telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    
    zip_buffer.seek(0)
    
    request_url = base_url + "send-email"
    
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field('text_message', text_message)
        data.add_field('receiver_email', receiver_email)
        data.add_field('subject', subject)
        data.add_field('zip_file', 
                      zip_buffer.read(),
                      filename=filename,
                      content_type='application/zip')
        
        async with session.post(
            request_url,
            data=data,
            headers={
                "X-Bot-Key": f"{BOT_API_KEY}",
                "X-User-ID": f"{telegram_id}",
            }
        ) as response:
            if response.status in (200, 201, 202, 203, 204):
                result = await response.json()
                logging.info(f"Email успешно отправлен на {receiver_email}")
                return result
            else:
                error_text = await response.text()
                logging.error(f"Ошибка отправки email: {response.status} - {error_text}")
                return {
                    "error": f"HTTP Error {response.status}",
                    "details": error_text[:100] if error_text else "No error details"
                }