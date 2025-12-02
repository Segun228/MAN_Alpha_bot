from aiogram import Bot
from aiogram.types import Message, ReactionTypeEmoji, ReactionTypeUnion

class ReactionManager:
    def __init__(self):
        pass

    async def add_reaction(self, bot: Bot, message: Message, emoji: str):
        """Добавить реакцию к сообщению"""
        try:
            reaction = ReactionTypeEmoji(emoji=emoji)
            
            await bot.set_message_reaction(
                chat_id=message.chat.id,
                message_id=message.message_id,
                reaction=[reaction]
            )
            return True
        except Exception as e:
            print(f"Не удалось поставить реакцию {emoji}: {e}")
            return False

    async def remove_reaction(self, bot: Bot, message: Message):
        """Убрать все реакции"""
        try:
            await bot.set_message_reaction(
                chat_id=message.chat.id,
                message_id=message.message_id,
                reaction=[]
            )
            return True
        except Exception as e:
            print(f"Не удалось убрать реакции: {e}")
            return False

    async def add_multiple_reactions(self, bot: Bot, message: Message, emojis: list):
        """Добавить несколько реакций"""
        try:
            reactions = [ReactionTypeEmoji(emoji=emoji) for emoji in emojis]
            await bot.set_message_reaction(
                chat_id=message.chat.id,
                message_id=message.message_id,
                reaction=reactions
            )
            return True
        except Exception as e:
            print(f"Не удалось поставить несколько реакций: {e}")
            return False
