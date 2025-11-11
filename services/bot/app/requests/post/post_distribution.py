import aiohttp
import asyncio
import os
import json
import logging
from dotenv import load_dotenv
from pprint import pprint
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DISTRIBUTION_CHOICES = (
    "normal",
    "binomial",
    "poisson",
    "uniform",
    "exponential",
    "beta",
    "gamma",
    "lognormal",
    "chi2",
    "t",
    "f",
    "geometric",
    "hypergeom",
    "negative_binomial",
)

async def post_distribution(telegram_id, name, distribution_type, distribution_parameters):
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
        exact_url = f"{base_url}api/distributions/" 
        logging.debug(f"Sending to {exact_url}")
        if isinstance(distribution_parameters, (dict, )):
            distribution_parameters = json.dumps(distribution_parameters)
        if distribution_type not in DISTRIBUTION_CHOICES:
            distribution_type = DISTRIBUTION_CHOICES[0]
            distribution_parameters = json.dumps({
                "mu":0,
                "sigma":1
            })
        data = {
            "name": name,
            "distribution_type":distribution_type,
            "distribution_parameters":distribution_parameters
        }
        async with session.post(
            exact_url, 
            headers={
                "Authorization": f"Bot {telegram_id}",
                "Content-Type": "application/json"
            },
            json=data
        ) as response:
            if response.status in (200, 201, 202, 203):
                logging.info("категории получены")
                return await response.json()
            else:
                return None


async def main():
    try:
        response_data = await post_distribution(telegram_id=6911237041, name="Тест через прогу", distribution_type="normal", distribution_parameters={"mu":0, "sigma":1})
        pprint(response_data)
    except ValueError:
        print("Пожалуйста, введите корректный числовой ID.")


if __name__ == "__main__":
    asyncio.run(main())