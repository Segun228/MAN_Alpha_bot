import aiohttp
import asyncio
import os
import io
import logging
from dotenv import load_dotenv
from pprint import pprint
import pandas as pd
import numpy as np
from sklearn.datasets import make_regression, make_classification, make_blobs
from io import BytesIO
from app.kafka.utils import build_log_message

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

async def fit_model(
    telegram_id,
    model_id,
    df:pd.DataFrame
):
    load_dotenv()
    base_url = os.getenv("BASE_URL")
    csv_buffer = io.BytesIO()
    df.to_csv(path_or_buf=csv_buffer, index=False)
    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    if csv_buffer is None:
        raise ValueError("CSV buffer is empty")

    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }

        exact_url = f"{base_url}ml-algorithms/model-fit/{model_id}/"
        logging.debug(f"Sending to {exact_url}")

        form = aiohttp.FormData()
        csv_buffer.seek(0)
        form.add_field(
            "file",
            csv_buffer,
            filename="refit.csv",
            content_type="text/csv"
        )

        async with session.post(
            exact_url,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=60),
            data=form
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("Датасет отправлен")
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
                logging.error(text)

async def refit_model(
    telegram_id,
    model_id,
    df:pd.DataFrame
):
    load_dotenv()
    base_url = os.getenv("BASE_URL")
    csv_buffer = io.BytesIO()
    df.to_csv(path_or_buf=csv_buffer,index=False)
    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    if csv_buffer is None:
        raise ValueError("CSV buffer is empty")

    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }

        exact_url = f"{base_url}ml-algorithms/model-refit/{model_id}/"
        logging.debug(f"Sending to {exact_url}")

        form = aiohttp.FormData()
        csv_buffer.seek(0)
        form.add_field(
            "file",
            csv_buffer,
            filename="refit.csv",
            content_type="text/csv"
        )

        async with session.post(
            exact_url,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=60),
            data=form
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("Датасет отправлен")
                await build_log_message(
                    telegram_id=telegram_id,
                    action="request",
                    platform="bot",
                    is_authenticated=True,
                    source="aiohttp",
                    level="INFO",
                    payload=str(exact_url)
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
                logging.error(text)


async def predict_model(    
    telegram_id,
    model_id,
    df:pd.DataFrame
):
    load_dotenv()
    base_url = os.getenv("BASE_URL")
    csv_buffer = io.BytesIO()
    df.to_csv(path_or_buf=csv_buffer,index=False)
    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    if not telegram_id:
        logging.error("No base telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    if csv_buffer is None:
        raise ValueError("CSV buffer is empty")

    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bot {telegram_id}",
        }

        exact_url = f"{base_url}ml-algorithms/model-predict/{model_id}/"
        logging.error(exact_url)
        logging.debug(f"Sending to {exact_url}")

        form = aiohttp.FormData()
        csv_buffer.seek(0)
        form.add_field(
            "file",
            csv_buffer,
            filename="refit.csv",
            content_type="text/csv"
        )

        async with session.post(
            exact_url,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=60),
            data=form
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("Датасет отправлен")
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
                logging.error(text)



def get_sample(
    task: str,
    n: int,
    noise: float,
    meaning_features: int,
    total_features: int,
    random_state: int = 42
) -> bytes:
    """
    Генерирует синтетические данные и возвращает CSV в байтах
    """
    np.random.seed(random_state)
    
    if task == "regression":
        X, y = make_regression(
            n_samples=n,
            n_features=total_features,
            n_informative=meaning_features,
            noise=noise,
            random_state=random_state
        )
        # Создаем DataFrame
        feature_cols = [f'feature_{i+1}' for i in range(total_features)]
        df = pd.DataFrame(X, columns=feature_cols)
        df['target'] = y
        
    elif task == "classification":
        X, y = make_classification(
            n_samples=n,
            n_features=total_features,
            n_informative=meaning_features,
            n_redundant=total_features - meaning_features,
            n_clusters_per_class=1,
            flip_y=noise,
            random_state=random_state
        )
        feature_cols = [f'feature_{i+1}' for i in range(total_features)]
        df = pd.DataFrame(X, columns=feature_cols)
        df['target'] = y
        
    elif task == "clusterization":
        X, y= make_blobs(
            n_samples=n,
            n_features=total_features,
            centers=meaning_features,
            cluster_std=noise * 10,
            random_state=random_state
        )
        feature_cols = [f'feature_{i+1}' for i in range(total_features)]
        df = pd.DataFrame(X, columns=feature_cols)
        df['cluster'] = y
        
    else:
        raise ValueError(f"Unknown task: {task}. Use 'regression', 'classification' or 'clusterization'")
    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    
    return buffer.getvalue()
