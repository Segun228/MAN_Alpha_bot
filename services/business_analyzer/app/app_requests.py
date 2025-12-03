import aiohttp
from dotenv import load_dotenv
import os
from fastapi import HTTPException
import logging


load_dotenv()


async def get_summary(
    context,
    business = "Малый бизнес",
    description = "Бизнес",
):
    SUMMARIZER_HOST = os.getenv("SUMMARIZER_HOST")
    SUMMARIZER_PORT = os.getenv("SUMMARIZER_PORT")
    if not SUMMARIZER_HOST:
        raise HTTPException(
            status_code=500,
            detail="No SUMMARIZER_HOST was provided in the env file"
        )
    if not SUMMARIZER_PORT:
        raise HTTPException(
            status_code=500,
            detail="No SUMMARIZER_PORT was provided in the env file"
        )
    URL = f"http://{SUMMARIZER_HOST}:{SUMMARIZER_PORT}/summarize/dialog"
    logging.info("Sending request to")
    PAYLOAD = {
        "context":context,
        "business":business,
        "description":description,
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                url = URL,
                json=PAYLOAD,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status not in (200, 201, 202, 203, 204, 205):
                    raise HTTPException(status_code=response.status)
                return await response.json()
        except aiohttp.ClientError as e:
            logging.error(e)
            raise HTTPException(detail=str(e), status_code=500)
        except HTTPException as e:
            logging.error(e)
            raise
        except Exception as e:
            logging.error(e)
            raise HTTPException(status_code=500)