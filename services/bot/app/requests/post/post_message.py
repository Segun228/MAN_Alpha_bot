import aiohttp
import os
import logging
from dotenv import load_dotenv

async def post_message(
    telegram_id,
    text,
    message_id,
    timestamp,
    direction,
    chat_type,
):
    load_dotenv()
    base_url = os.getenv("BASE_DB_SERVICE_URL")
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
    
    request_url = base_url + "messages"
    logging.info(f"Sending request to {request_url}")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            request_url,
            json={
                "telegram_id": telegram_id,
                "message_id": message_id,
                "message": text,
                "direction": direction,
                "chat_type": chat_type,
                "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp)
            },
            headers={
                "X-Bot-Key": BOT_API_KEY,
                "Content-Type": "application/json" 
            },
        ) as response:
            if response.status in (200, 201, 202, 203, 204):
                data = await response.json()
                logging.info("Message successfully saved!")
                return data
            else:
                logging.error(f"HTTP error: {response.status}")
                request_body = {
                    "telegram_id": telegram_id,
                    "message_id": message_id,
                    "message": text,
                    "direction": direction,
                    "chat_type": chat_type,
                    "timestamp": timestamp
                }
                logging.error(f"Request body: {request_body}")
                
                try:
                    error_data = await response.json()
                    logging.error(f"Error details: {error_data}")
                except Exception as e:
                    logging.exception(e)
                    error_text = await response.text()
                    logging.error(f"Failed to parse JSON. Response text: {error_text}")
                return None