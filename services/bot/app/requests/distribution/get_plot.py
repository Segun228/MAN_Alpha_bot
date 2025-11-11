import aiohttp
import asyncio
import os
import logging
from dotenv import load_dotenv
from pprint import pprint
from app.kafka.utils import build_log_message
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def get_plot( 
        telegram_id, 
        id
    ):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
        
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }
        exact_url = f"{base_url}distributions/plot/{id}/" 
        logging.debug(f"Sending to {exact_url}")
        async with session.post(
            exact_url, 
            headers=headers,
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("изображение получено")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=str(exact_url)
                )
                return await response.read()
            else:
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = response.text
                )
                return None


async def get_probability( 
        telegram_id, 
        id,
        a=0.0
    ):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
        
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }
        data = {
            "a":a
        }
        exact_url = f"{base_url}distributions/probability/{id}/" 
        logging.debug(f"Sending to {exact_url}")
        async with session.post(
            exact_url, 
            headers=headers,
            data=data
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("изображение получено")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=str(exact_url)
                )
                return await response.read()
            else:
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = response.text
                )
                return None


async def get_interval( 
        telegram_id, 
        id,
        a=-1.0,
        b=1.0
    ):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
        
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }
        data = {
            "a":a,
            "b":b
        }
        exact_url = f"{base_url}distributions/interval/{id}/"
        logging.debug(f"Sending to {exact_url}")
        async with session.post(
            exact_url, 
            headers=headers,
            data=data
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("изображение получено")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=str(exact_url)
                )
                return await response.read()
            else:
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = response.text
                )
                return None


async def get_quantile( 
        telegram_id, 
        id,
        a = 0.5
    ):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
        
    async with aiohttp.ClientSession() as session:
        if a>1:
            a = a/100
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }
        data = {
            "quantile":a
        }
        exact_url = f"{base_url}distributions/quantile/{id}/" 
        logging.debug(f"Sending to {exact_url}")
        async with session.post(
            exact_url, 
            headers=headers,
            data=data
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("изображение получено")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=str(exact_url)
                )
                return await response.read()
            else:
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = response.text
                )
                return None


async def get_percentile( 
        telegram_id, 
        id,
        a = 50.0
    ):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
        
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }
        data = {
            "percentile":a
        }
        exact_url = f"{base_url}distributions/percentile/{id}/" 
        logging.debug(f"Sending to {exact_url}")
        async with session.post(
            exact_url, 
            headers=headers,
            data = data
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("изображение получено")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=str(exact_url)
                )
                return await response.read()
            else:
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = response.text
                )
                return None


async def get_sample( 
        telegram_id, 
        id,
        n=1000
    ):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
        
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }
        data = {
            "n":n
        }
        exact_url = f"{base_url}distributions/sample/{id}/" 
        logging.debug(f"Sending to {exact_url}")
        async with session.post(
            exact_url, 
            headers=headers,
            data = data
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("изображение получено")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=str(exact_url)
                )
                return await response.read()
            else:
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = response.text
                )
                return None