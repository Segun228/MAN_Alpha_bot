import asyncio
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit: float = 1.0):
        super().__init__()
        self.rate_limit = limit
        self.user_timestamps = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id #type:ignore
        now = asyncio.get_event_loop().time()

        last_time = self.user_timestamps.get(user_id, 0)
        
        if now - last_time < self.rate_limit:
            await event.answer("⏳ Слишком быстро, подожди немного.")
            return 
        
        self.user_timestamps[user_id] = now

        return await handler(event, data)