import aiohttp
import asyncio
import os
import logging
from dotenv import load_dotenv
from pprint import pprint
from io import BytesIO
from app.kafka.utils import build_log_message

async def count_n(
    telegram_id,
    id,
    mde = 5.0
):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id or not id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }

        exact_url = f"{base_url}ab-tests/sample-size/{id}/"
        logging.debug(f"Sending to {exact_url}")

        data = {
            "mde":mde
        }
        async with session.post(
            exact_url,
            headers=headers,
            json=data
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("Результат получен")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=str(data)
                )
                return await response.json()
            else:
                text = await response.text()
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = text
                )
                logging.error(f"Ошибка {response.status}: {text}")
                return None


async def count_mde(
    telegram_id,
    id,
):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id or not id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }

        exact_url = f"{base_url}ab-tests/mde/{id}/"
        logging.debug(f"Sending to {exact_url}")

        async with session.post(
            exact_url,
            headers=headers,
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("Результат получен")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=exact_url
                )
                return await response.json()
            else:
                text = await response.text()
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = text
                )
                logging.error(f"Ошибка {response.status}: {text}")
                return None


async def z_test(
    telegram_id,
    id,
):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id or not id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }

        exact_url = f"{base_url}ab-tests/z-test/{id}/"
        logging.debug(f"Sending to {exact_url}")

        async with session.post(
            exact_url,
            headers=headers,
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("Результат получен")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=exact_url
                )
                return await response.json()
            else:
                text = await response.text()
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = text
                )
                logging.error(f"Ошибка {response.status}: {text}")
                return None



async def t_test(
    telegram_id,
    id,
):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id or not id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }

        exact_url = f"{base_url}ab-tests/t-test/{id}/"
        logging.debug(f"Sending to {exact_url}")

        async with session.post(
            exact_url,
            headers=headers,
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("Результат получен")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=exact_url
                )
                return await response.json()
            else:
                text = await response.text()
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = text
                )
                logging.error(f"Ошибка {response.status}: {text}")
                return None


async def chi2_test(
    telegram_id,
    id,
):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id or not id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }

        exact_url = f"{base_url}ab-tests/chi-square-2sample/{id}/"
        logging.debug(f"Sending to {exact_url}")
        async with session.post(
            exact_url,
            headers=headers,
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("Результат получен")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=exact_url
                )
                return await response.json()
            else:
                text = await response.text()
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = text
                )
                logging.error(f"Ошибка {response.status}: {text}")
                return None


async def u_test(
    telegram_id,
    id,
):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id or not id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }

        exact_url = f"{base_url}ab-tests/u-test/{id}/"
        logging.debug(f"Sending to {exact_url}")

        async with session.post(
            exact_url,
            headers=headers,
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("Результат получен")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=exact_url
                )
                return await response.json()
            else:
                text = await response.text()
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = text
                )
                logging.error(f"Ошибка {response.status}: {text}")
                return None


async def welch_test(
    telegram_id,
    id,
):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id or not id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }

        exact_url = f"{base_url}ab-tests/welch-test/{id}/"
        logging.debug(f"Sending to {exact_url}")

        async with session.post(
            exact_url,
            headers=headers,
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("Результат получен")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=exact_url
                )
                return await response.json()
            else:
                text = await response.text()
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = text
                )
                logging.error(f"Ошибка {response.status}: {text}")
                return None



async def ad_test(
    telegram_id,
    id,
):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id or not id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }
        exact_url = f"{base_url}ab-tests/anderson-darling-test/{id}/"
        logging.debug(f"Sending to {exact_url}")

        async with session.post(
            exact_url,
            headers=headers,
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("Результат получен")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=exact_url
                )
                return await response.json()
            else:
                text = await response.text()
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = text
                )
                logging.error(f"Ошибка {response.status}: {text}")
                return None


async def cramer_test(
    telegram_id,
    id,
):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id or not id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }
        exact_url = f"{base_url}ab-tests/cramer-test/{id}/"
        logging.debug(f"Sending to {exact_url}")

        async with session.post(
            exact_url,
            headers=headers,
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("Результат получен")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=exact_url
                )
                return await response.json()
            else:
                text = await response.text()
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = text
                )
                logging.error(f"Ошибка {response.status}: {text}")
                return None


async def ks_test(
    telegram_id,
    id,
):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id or not id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }
        exact_url = f"{base_url}ab-tests/cramer-test/{id}/"
        logging.debug(f"Sending to {exact_url}")

        async with session.post(
            exact_url,
            headers=headers,
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("Результат получен")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=exact_url
                )
                return await response.json()
            else:
                text = await response.text()
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = text
                )
                logging.error(f"Ошибка {response.status}: {text}")
                return None




async def sw_test(
    telegram_id,
    id,
):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id or not id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }
        exact_url = f"{base_url}ab-tests/shapiro-wilk-test/{id}/"
        logging.debug(f"Sending to {exact_url}")


        async with session.post(
            exact_url,
            headers=headers,
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("Результат получен")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=exact_url
                )
                return await response.json()
            else:
                text = await response.text()
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = text
                )
                logging.error(f"Ошибка {response.status}: {text}")
                return None


async def ll_test(
    telegram_id,
    id,
):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id or not id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }
        exact_url = f"{base_url}ab-tests/lilliefors-test/{id}/"
        logging.debug(f"Sending to {exact_url}")

        async with session.post(
            exact_url,
            headers=headers,
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("Результат получен")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=exact_url
                )
                return await response.json()
            else:
                text = await response.text()
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = text
                )
                logging.error(f"Ошибка {response.status}: {text}")
                return None



async def bootstrap(
    telegram_id,
    id,
    iterations = 10000
):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id or not id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }
        data = {
            "iterations":iterations
        }
        exact_url = f"{base_url}ab-tests/bootstrap/{id}/"
        logging.debug(f"Sending to {exact_url}")

        async with session.post(
            exact_url,
            data=data,
            headers=headers,
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("Результат получен")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=exact_url
                )
                return await response.json()
            else:
                text = await response.text()
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = text
                )
                logging.error(f"Ошибка {response.status}: {text}")
                return None






async def anova(
    telegram_id,
    id,
):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id or not id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }
        exact_url = f"{base_url}ab-tests/anova/{id}/"
        logging.debug(f"Sending to {exact_url}")

        async with session.post(
            exact_url,
            headers=headers,
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("Результат получен")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=exact_url
                )
                return await response.json()
            else:
                text = await response.text()
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = text
                )
                logging.error(f"Ошибка {response.status}: {text}")
                return None



async def cuped(
    telegram_id,
    id,
    history_column,
    history_df
):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id or not id:
        logging.error("Missing required parameters")
        raise ValueError("telegram_id or id missing")

    buffer = BytesIO()
    history_df.to_csv(buffer, index=False)
    buffer.seek(0)

    form = aiohttp.FormData()
    form.add_field("column_name", history_column)
    form.add_field("file",
        buffer,
        filename="history.csv",
        content_type="text/csv"
    )

    exact_url = f"{base_url}ab-tests/cuped/{id}/"
    logging.debug(f"Sending to {exact_url}")

    headers = {
        "Authorization": f"Bot {telegram_id}",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            exact_url,
            headers=headers,
            data=form
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("Результат получен")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=exact_url
                )
                return await response.json()
            else:
                text = await response.text()
                logging.error(f"Ошибка {response.status}: {text}")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = text
                )
                return None


async def cupac(
    telegram_id,
    id,
    feature_columns,
    target_metric,
    history_df
):
    load_dotenv()
    base_url = os.getenv("BASE_URL")

    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id or not id:
        logging.error("telegram_id or id missing")
        raise ValueError("Missing parameters")


    buffer = BytesIO()
    history_df.to_csv(buffer, index=False)
    buffer.seek(0)


    form = aiohttp.FormData()
    form.add_field("target_metric", target_metric)
    for col in feature_columns:
        form.add_field("feature_columns", col)
    form.add_field(
        "history_file",
        buffer,
        filename="history.csv",
        content_type="text/csv"
    )

    headers = {
        "Authorization": f"Bot {telegram_id}",
    }
    exact_url = f"{base_url}ab-tests/cupac/{id}/"
    logging.debug(f"Sending to {exact_url}")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            exact_url,
            headers=headers,
            data=form
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("Результат получен")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=exact_url
                )
                return await response.json()
            else:
                text = await response.text()
                logging.error(f"Ошибка {response.status}: {text}")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp error handler",
                    level="ERROR",
                    payload = text
                )
                return None