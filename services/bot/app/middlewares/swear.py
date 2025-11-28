from app.utils.check_swear import chech_swearing_number
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable

class SwearMiddleware(BaseMiddleware):
    def __init__(self, threshold: int = 0):
        self.threshold = threshold
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.text and chech_swearing_number(event.text) > self.threshold:
            await event.answer(
                "🤫 Не материтесь, пожалуйста!\n\n"
                "Мы не против мата, но он может мешать моделям вас понимать\n"
                f"Нашли у вас {chech_swearing_number(event.text)} нецензурных слов\n"
            )
            return
        if event.caption and chech_swearing_number(event.caption) > self.threshold:
            await event.answer(
                "🤫 Не материтесь, пожалуйста!\n\n"
                "Мы не против мата, но он может мешать моделям вас понимать\n"
                f"Нашли у вас {chech_swearing_number(event.caption)} нецензурных слов\n"
            )
            return
        return await handler(event, data)

