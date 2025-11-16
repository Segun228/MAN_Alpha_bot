from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable

class MessageLengthMiddleware(BaseMiddleware):
    def __init__(self, max_length: int = 4000):
        self.max_length = max_length
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.text and len(event.text) > self.max_length:
            await event.answer(
                f"❌ Сообщение слишком длинное. "
                f"Максимум {self.max_length} символов.\n"
                f"Ваше сообщение: {len(event.text)} символов."
            )
            return
        if event.caption and len(event.caption) > self.max_length:
            await event.answer(
                f"❌ Подпись к медиа слишком длинная. "
                f"Максимум {self.max_length} символов.\n"
                f"Ваша подпись: {len(event.caption)} символов."
            )
            return
        return await handler(event, data)


def setup_middlewares(dp, max_length: int = 4000):
    dp.message.middleware(MessageLengthMiddleware(max_length))