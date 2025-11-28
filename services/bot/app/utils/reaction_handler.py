from aiogram import Bot
from aiogram.types import Message, ReactionTypeEmoji

class ReactionManager:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def add_reaction(self, message: Message, emoji: str):
        """Добавить реакцию к сообщению"""
        try:
            reaction = ReactionTypeEmoji(emoji=emoji)
            
            await self.bot.set_message_reaction(
                chat_id=message.chat.id,
                message_id=message.message_id,
                reaction=[reaction]
            )
            return True
        except Exception as e:
            print(f"Не удалось поставить реакцию {emoji}: {e}")
            return False

    async def remove_reaction(self, message: Message):
        """Убрать все реакции"""
        try:
            await self.bot.set_message_reaction(
                chat_id=message.chat.id,
                message_id=message.message_id,
                reaction=[]
            )
            return True
        except Exception as e:
            print(f"Не удалось убрать реакции: {e}")
            return False

    async def add_multiple_reactions(self, message: Message, emojis: list):
        """Добавить несколько реакций"""
        try:
            reactions = [ReactionTypeEmoji(emoji=emoji) for emoji in emojis]
            await self.bot.set_message_reaction(
                chat_id=message.chat.id,
                message_id=message.message_id,
                reaction=reactions
            )
            return True
        except Exception as e:
            print(f"Не удалось поставить несколько реакций: {e}")
            return False
