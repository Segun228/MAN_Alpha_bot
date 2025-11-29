from app.utils.defend_prompt import defend_prompt
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
import logging

class DefenderMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        logging.info("Defender middleware is being called")
        if event.text:
            is_safe = await defend_prompt(event.text)
            logging.info(f"🎯{is_safe}")
            if not is_safe:
                logging.info(f"🚫 Опасный запрос (text): {event.text}")
                await event.answer(
                    "🤫 Попробуйте переформулировать ваш вопрос, пожалуйста!\n\nНам показалось что он может быть вредоносным..."
                )
                return
            else:
                logging.info(f"✅ Безопасный запрос (text): {event.text}")
        
        if event.caption:
            is_safe = await defend_prompt(event.caption)
            if not is_safe:
                logging.info(f"🚫 Опасный запрос (caption): {event.caption}")
                await event.answer(
                    "🤫 Попробуйте переформулировать ваш вопрос, пожалуйста!\n\nНам показалось что он может быть вредоносным..."
                )
                return
            else:
                logging.info(f"✅ Безопасный запрос (caption): {event.caption}")
        
        return await handler(event, data)