from app.utils.defend_prompt import defend_prompt
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
import logging

from app.utils.reaction_handler import ReactionManager
reactioner = ReactionManager()

class DefenderMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        bot = data.get("bot")
        if not bot:
            raise ValueError("Could not get the bot")
        if event.voice:
            try:
                file = await bot.get_file(event.voice.file_id)
                audio_stream = await bot.download_file(file.file_path)
                
                try:
                    audio_bytes = await audio_stream.read()
                    
                    from app.requests.post.post_audio import send_audio
                    result = await send_audio(audio_bytes, event.from_user.id)
                    
                    if result and "text" in result:
                        text = result["text"].strip()
                        is_safe = await defend_prompt(text)
                        if not is_safe:
                            await event.answer(
                                "🤫 Попробуйте переформулировать ваш вопрос, пожалуйста!\n\nНам показалось что он может быть вредоносным..."
                            )
                            await reactioner.add_reaction(
                                bot=bot,
                                message=event,
                                emoji="💩"
                            )
                            return
                        data["recognized_text"] = text
                finally:
                    await audio_stream.close()
            except Exception as e:
                logging.error(f"Voice processing error: {e}")
        
        elif event.video_note:
            try:
                file = await bot.get_file(event.video_note.file_id)
                video_stream = await bot.download_file(file.file_path)
                
                try:
                    video_bytes = await video_stream.read()
                    
                    from app.requests.post.post_audio import send_audio
                    result = await send_audio(video_bytes, event.from_user.id)
                    
                    if result and "text" in result:
                        text = result["text"].strip()
                        is_safe = await defend_prompt(text)
                        if not is_safe:
                            await event.answer(
                                "🤫 Попробуйте переформулировать ваш вопрос, пожалуйста!\n\nНам показалось что он может быть вредоносным..."
                            )
                            return
                        data["recognized_text"] = text
                finally:
                    await video_stream.close()
            except Exception as e:
                logging.error(f"Video note processing error: {e}")
        
        elif event.text:
            is_safe = await defend_prompt(event.text)
            if not is_safe:
                await event.answer(
                    "🤫 Попробуйте переформулировать ваш вопрос, пожалуйста!\n\nНам показалось что он может быть вредоносным..."
                )
                return
        
        elif event.caption:
            is_safe = await defend_prompt(event.caption)
            if not is_safe:
                await event.answer(
                    "🤫 Попробуйте переформулировать ваш вопрос, пожалуйста!\n\nНам показалось что он может быть вредоносным..."
                )
                return
        
        return await handler(event, data)