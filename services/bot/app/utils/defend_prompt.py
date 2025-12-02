import aiohttp
import os
import logging
from dotenv import load_dotenv

async def defend_prompt(
    prompt
)->bool:
    load_dotenv()
    base_url = "http://defender:8088"
    
    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    
    request_url = base_url + "/defend"
    logging.info(f"Sending request to {request_url}")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            request_url,
            json={
                "prompt":prompt
            },
            headers={
                "Content-Type": "application/json" 
            },
        ) as response:
            if response.status in (200, 201, 202, 203, 204):
                data = await response.json()
                logging.info("Message successfully saved!")
                result = data.get("is_safe")
                logging.info(data)
                logging.info(result)
                if not result or result is None or (isinstance(result, str) and result.strip().lower() not in ("true", "t", "yes")):
                    result = False
                else:
                    result = True
                return result
            else:
                logging.error(f"HTTP error: {response.status}")
                request_body = {
                    "prompt":prompt
                }
                logging.error(f"Request body: {request_body}")
                
                try:
                    error_data = await response.json()
                    logging.error(f"Error details: {error_data}")
                except Exception as e:
                    logging.exception(e)
                    error_text = await response.text()
                    logging.error(f"Failed to parse JSON. Response text: {error_text}")
                return None