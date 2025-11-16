from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
import logging
import datetime
from app.requests.post.post_message import post_message

def validate_param(object, obj_type = None)->Any|None:
    if object is None:
        raise ValueError("Error failed for None")
    if obj_type and not isinstance(object, obj_type):
        raise ValueError("Error failed for generic")
    if isinstance(object, (tuple, list)) and len(object) == 0:
        raise ValueError("Error failed for list/tuple")
    if isinstance(object, (str, )) and not object.strip():
        raise ValueError("Error failed for str")
    return object



class TextMessageLoggerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:

        if event.text:
            await self.log_user_message(event)
        response = await handler(event, data)
        if response and isinstance(response, Message) and response.text:
            await self.log_bot_response(event, response)
        return response

    async def log_user_message(self, event: Message) -> None:
        try:
            message_data = {
                "telegram_id": event.from_user.id,
                "text": event.text,
                "message_id": event.message_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "direction": "question",
                "chat_type": event.chat.type
            }
            await self.save_to_db(message_data)
            logging.info(f"Logged user message from {event.from_user.id}")
        except Exception as e:
            logging.error(f"Error logging user message: {e}")

    async def log_bot_response(self, event: Message, response: Message) -> None:
        try:
            response_data = {
                "telegram_id": event.from_user.id,
                "text": response.text,
                "message_id": response.message_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "direction": "answer", 
                "chat_type": event.chat.type,
            }
            await self.save_to_db(response_data)
            logging.info(f"Logged bot response to {event.from_user.id}")
        except Exception as e:
            logging.error(f"Error logging bot response: {e}")
    
    async def save_to_db(self, message_data: Dict) -> None:
        try:
            telegram_id = validate_param(message_data.get("telegram_id"))
            text = validate_param(message_data.get("text"))
            message_id = validate_param(message_data.get("message_id"))
            timestamp = validate_param(message_data.get("timestamp"))
            direction = validate_param(message_data.get("direction", "question"))
            chat_type = validate_param(message_data.get("chat_type"))
            result = await post_message(
                telegram_id=telegram_id,
                text = text,
                message_id = message_id,
                timestamp = timestamp,
                direction = direction,
                chat_type = chat_type
            )
            if result is None:
                logging.error("Error while sending a message to the DB service")
            else:
                logging.info("Message sent to the DB_service succesfully")
        except Exception as e:
            logging.error(f"Error saving to DB: {e}")