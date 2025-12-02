import aiohttp
import os
import logging
import asyncio
from dotenv import load_dotenv

async def send_audio(
    audio: bytes,
    telegram_id: int
) -> dict|None:
    """
    Отправляет аудиофайл на сервис распознавания речи (STT)
    
    Args:
        audio: аудиофайл в виде bytes
        telegram_id: ID пользователя Telegram
    
    Returns:
        dict: результат распознавания или информация об ошибке
    """
    load_dotenv()
    
    base_url = os.getenv("SPEECH_SERVICE_URL", "http://speech-service:8096/")
    BOT_API_KEY = os.getenv("BOT_API_KEY")
    
    if not base_url:
        logging.error("No base URL was provided")
        raise ValueError("No base URL was provided")
    
    if not BOT_API_KEY:
        logging.error("No BOT_API_KEY was provided")
        raise ValueError("No BOT_API_KEY was provided")
    
    if not audio:
        logging.error("No audio data was provided")
        raise ValueError("No audio data was provided")
    
    if not telegram_id:
        logging.error("No telegram_id was provided")
        raise ValueError("No telegram_id was provided")
    
    base_url = base_url.rstrip('/')
    request_url = f"{base_url}/stt"
    
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        
        data.add_field(
            'file',
            audio,
            filename='audio.ogg',
            content_type='audio/ogg'
        )
        
        try:
            async with session.post(
                request_url,
                data=data,
                headers={
                    "X-Bot-Key": str(BOT_API_KEY),
                    "X-User-ID": str(telegram_id),
                    "Accept": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=500)
            ) as response:
                response_text = await response.text()
                
                if response.status in (200, 201, 202, 203, 204):
                    try:
                        result = await response.json()
                        logging.info(f"Речь успешно расшифрована для пользователя {telegram_id}")
                        return result.get("text") if isinstance(result, dict) else result
                    except Exception as json_error:
                        logging.error(f"Ошибка парсинга JSON: {json_error}, ответ: {response_text[:200]}")
                        return {
                            "error": "Invalid JSON response",
                            "raw_response": response_text[:500],
                            "status_code": response.status
                        }
                else:
                    logging.error(
                        f"Ошибка отправки аудио. "
                        f"Статус: {response.status}, "
                        f"Ответ: {response_text[:500]}"
                    )
                    return {
                        "error": f"HTTP Error {response.status}",
                        "details": response_text[:500] if response_text else "No error details",
                        "status_code": response.status
                    }
                    
        except aiohttp.ClientError as e:
            logging.error(f"Network error while sending audio: {e}")
            return {
                "error": "Network error",
                "details": str(e)
            }
        except asyncio.TimeoutError:
            logging.error("Request timeout while sending audio")
            return {
                "error": "Request timeout",
                "details": "Service did not respond within 30 seconds"
            }
        except Exception as e:
            logging.error(f"Unexpected error in send_audio: {e}")
            return {
                "error": "Internal error",
                "details": str(e)
            }