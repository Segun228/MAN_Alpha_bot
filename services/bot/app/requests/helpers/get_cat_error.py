import aiohttp
import logging

async def get_cat_error_async():
    base_url = "https://http.cat/404"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(base_url) as response:
                response.raise_for_status()
                return await response.read()
        except aiohttp.ClientError as e:
            logging.error(f"Ошибка при запросе к http.cat: {e}")
            return None