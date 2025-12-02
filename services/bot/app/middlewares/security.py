from app.utils.check_prompt import check_prompt_number
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
from aiogram import Router, Bot
from app.requests.post.post_audio import send_audio
from app.utils.check_prompt import check_prompt_number
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
from aiogram import Bot
from app.requests.post.post_audio import send_audio
import logging
from app.utils.reaction_handler import ReactionManager
reactioner = ReactionManager()



class SecurityMiddleware(BaseMiddleware):
    def __init__(self, threshold: int = 0):
        self.threshold = threshold
        self.logger = logging.getLogger(__name__)
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        """
        Middleware для проверки безопасности входящих сообщений
        """
        try:
            bot: Bot|None = data.get("bot")
            if not bot:
                self.logger.error("Bot instance not found in data")
                return await handler(event, data)
            
            text_to_check = None
            if event.text:
                text_to_check = event.text
            elif event.caption:
                text_to_check = event.caption
            elif event.voice:
                text_to_check = await self._process_voice_message(event, bot)
            if text_to_check:
                if check_prompt_number(text_to_check) > self.threshold:
                    await event.answer(
                        "🤫 Попробуйте переформулировать ваш вопрос, пожалуйста!"
                    )
                    await reactioner.add_reaction(
                        bot=bot,
                        message=event,
                        emoji="💩"
                    )
                    return
                if event.voice and isinstance(text_to_check, str):
                    data["recognized_text"] = text_to_check
            return await handler(event, data)
        except Exception as e:
            self.logger.error(f"Security middleware error: {e}")
            return await handler(event, data)
    
    async def _process_voice_message(self, event: Message, bot: Bot) -> str:
        """
        Обрабатывает голосовое сообщение и возвращает распознанный текст
        """
        try:
            file_id = event.voice.file_id
            file = await bot.get_file(file_id)
            audio_stream = await bot.download_file(file.file_path)
            if not audio_stream:
                self.logger.error("Failed to download voice file")
                return ""
            try:
                audio_bytes = audio_stream.read()
                
                if not audio_bytes:
                    self.logger.error("Empty audio file")
                    return ""
                
                result = await send_audio(audio_bytes, telegram_id=event.from_user.id)
                
                if not result or "error" in result:
                    error_msg = result.get("error", "Unknown error") if result else "No response"
                    self.logger.error(f"STT error: {error_msg}")
                    return ""
                
                if "text" in result and result["text"]:
                    return str(result["text"]).strip()
                else:
                    self.logger.warning("No text in STT response")
                    return ""
            finally:
                audio_stream.close()
        except Exception as e:
            self.logger.error(f"Error processing voice message: {e}")
            return ""