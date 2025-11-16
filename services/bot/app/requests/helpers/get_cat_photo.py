import aiohttp
from aiogram.types import URLInputFile
from dotenv import load_dotenv
import os
import logging
from aiogram import Bot

load_dotenv()

async def get_cat_photo(bot:Bot, chat_id:int):
    CAT_API_KEY = os.getenv("CAT_API_KEY")
    if not CAT_API_KEY:
        logging.error("Error while getting CAT_API_KEY variable from .env")
        return None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                'https://api.thecatapi.com/v1/images/search',
                headers={'x-api-key': CAT_API_KEY}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    cat_url = data[0]['url']
                    
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=URLInputFile(cat_url),
                        caption="Получайте котика! 🐾"
                    )
                else:
                    await bot.send_message(chat_id, "Хотели отправить вам котика, но они все спят, попробуйте позже 😴")
                    
    except Exception as e:
        logging.error(f"Error getting cat: {e}")
        await bot.send_message(chat_id, "Не удалось найти котика 😿")