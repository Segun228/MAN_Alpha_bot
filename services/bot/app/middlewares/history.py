from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
import logging
import datetime

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
        """Твоя функция для сохранения в БД"""
        try:
            #TODO
            pass
        except Exception as e:
            logging.error(f"Error saving to DB: {e}")