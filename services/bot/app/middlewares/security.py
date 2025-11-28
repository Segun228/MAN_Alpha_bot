from app.utils.check_prompt import check_prompt_number
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable

class SecurityMiddleware(BaseMiddleware):
    def __init__(self, threshold: int = 0):
        self.threshold = threshold
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.text and check_prompt_number(event.text) > self.threshold:
            await event.answer(
                "🤫 Попробуйте переформулировать ваш вопрос, пожалуйста!"
            )
            return
        if event.caption and check_prompt_number(event.caption) > self.threshold:
            await event.answer(
                "🤫 Попробуйте переформулировать ваш вопрос, пожалуйста!"
            )
            return
        return await handler(event, data)
