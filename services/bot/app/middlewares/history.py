from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
import logging
import datetime
from app.requests.post.post_message import post_message
import uuid
from contextvars import ContextVar

def validate_param(object, obj_type = None)->Any|None:
    if object is None:
        raise ValueError("Error failed for None")
    if obj_type and not isinstance(object, obj_type):
        raise ValueError("Error failed for generic")
    if isinstance(object, (tuple, list)) and len(object) == 0:
        raise ValueError("Error failed for list/tuple")
    if isinstance(object, (str, )) and not object.strip():
        raise ValueError("Error failed for str")
    return object

message_chain_id: ContextVar[str] = ContextVar('message_chain_id', default='')

class TextMessageLoggerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        chain_id = str(uuid.uuid4())[:8]
        message_chain_id.set(chain_id)
        
        logging.info(f"🔄 [{chain_id}] Middleware started for user {event.from_user.id}")

        if event.text:
            logging.info(f"💬 [{chain_id}] Processing user message: '{event.text[:50]}...'")
            await self.log_user_message(event, chain_id)
        else:
            logging.warning(f"⚠️ [{chain_id}] Message without text from user {event.from_user.id}")

        try:
            response = await handler(event, data)
            logging.info(f"✅ [{chain_id}] Handler executed successfully")
            
            if response and isinstance(response, Message) and response.text:
                logging.info(f"🤖 [{chain_id}] Bot response generated: '{response.text[:50]}...'")
                await self.log_bot_response(event, response, chain_id)
            else:
                logging.warning(f"⚠️ [{chain_id}] No text response from handler for user {event.from_user.id}")
                
            return response
            
        except Exception as e:
            logging.error(f"💥 [{chain_id}] Error in handler for user {event.from_user.id}: {e}", exc_info=True)
            raise

    async def log_user_message(self, event: Message, chain_id: str = "") -> None:
        try:
            message_data = {
                "telegram_id": event.from_user.id,
                "text": event.text,
                "message_id": event.message_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "direction": "question",
                "chat_type": event.chat.type
            }
            logging.debug(f"📝 [{chain_id}] Saving user message to DB: {message_data}")
            await self.save_to_db(message_data, chain_id)
            logging.info(f"✅ [{chain_id}] User message logged successfully for {event.from_user.id}")
        except Exception as e:
            logging.error(f"❌ [{chain_id}] Error logging user message: {e}", exc_info=True)

    async def log_bot_response(self, event: Message, response: Message, chain_id: str = "") -> None:
        try:
            response_data = {
                "telegram_id": event.from_user.id,
                "text": response.text,
                "message_id": response.message_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "direction": "answer", 
                "chat_type": event.chat.type,
            }
            logging.debug(f"📝 [{chain_id}] Saving bot response to DB: {response_data}")
            await self.save_to_db(response_data, chain_id)
            logging.info(f"✅ [{chain_id}] Bot response logged successfully for {event.from_user.id}")
        except Exception as e:
            logging.error(f"❌ [{chain_id}] Error logging bot response: {e}", exc_info=True)
    
    async def save_to_db(self, message_data: Dict, chain_id: str = "") -> None:
        try:
            telegram_id = validate_param(message_data.get("telegram_id"))
            text = validate_param(message_data.get("text"))
            message_id = validate_param(message_data.get("message_id"))
            timestamp = validate_param(message_data.get("timestamp"))
            direction = validate_param(message_data.get("direction", "question"))
            chat_type = validate_param(message_data.get("chat_type"))
            
            logging.debug(f"🌐 [{chain_id}] Sending to DB service: user={telegram_id}, direction={direction}")
            
            result = await post_message(
                telegram_id=telegram_id,
                text=text,
                message_id=message_id,
                timestamp=timestamp,
                direction=direction,
                chat_type=chat_type
            )
            
            if result is None:
                logging.error(f"❌ [{chain_id}] DB service returned None for user {telegram_id}")
            else:
                logging.info(f"✅ [{chain_id}] Message sent to DB service successfully for user {telegram_id}")
                
        except Exception as e:
            logging.error(f"💥 [{chain_id}] Error saving to DB: {e}", exc_info=True)

class BotReplyLogger():
    async def __call__(
        self,
        telegram_id: int,
        text: str,
        business_id: int|None = None,
        context: str = "direct"
    ) -> Any:
        chain_id = message_chain_id.get() or str(uuid.uuid4())[:8]
        
        logging.info(f"🔧 [{chain_id}] BotReplyLogger called for user {telegram_id} from {context}")
        
        try:
            if telegram_id and text:
                logging.info(f"💬 [{chain_id}] Processing bot reply: '{text[:50]}...'")
                await self.log_bot_response(
                    telegram_id=telegram_id,
                    text=text,
                    chain_id=chain_id,
                    business_id = business_id
                )
                logging.info(f"✅ [{chain_id}] Bot reply processed successfully")
            else:
                logging.warning(f"⚠️ [{chain_id}] Invalid parameters: telegram_id={telegram_id}, text_length={len(text) if text else 0}")
                
        except Exception as e:
            logging.error(f"💥 [{chain_id}] Error in BotReplyLogger: {e}", exc_info=True)
            raise

    async def log_bot_response(
        self, 
        telegram_id: int,
        text: str,
        business_id: int|None = None,
        chain_id: str = ""
    ) -> None:
        try:
            response_data = {
                "telegram_id": telegram_id,
                "text": text,
                "message_id": 777,
                "timestamp": datetime.datetime.now().isoformat(),
                "direction": "answer", 
                "chat_type": "private",
                "business_id": business_id
            }
            logging.debug(f"📝 [{chain_id}] Saving LLM response to DB: {response_data}")
            await self.save_to_db(response_data, chain_id)
            logging.info(f"✅ [{chain_id}] LLM response logged successfully for user {telegram_id}")
        except Exception as e:
            logging.error(f"❌ [{chain_id}] Error logging LLM response: {e}", exc_info=True)
    
    async def save_to_db(self, message_data: Dict, chain_id: str = "") -> None:
        try:
            telegram_id = validate_param(message_data.get("telegram_id"))
            text = validate_param(message_data.get("text"))
            message_id = validate_param(message_data.get("message_id"))
            timestamp = validate_param(message_data.get("timestamp"))
            direction = validate_param(message_data.get("direction", "question"))
            chat_type = validate_param(message_data.get("chat_type"))
            business_id = message_data.get("business_id")
            logging.debug(f"🌐 [{chain_id}] Sending LLM response to DB service: user={telegram_id}")
            
            result = await post_message(
                telegram_id=telegram_id,
                text=text,
                message_id=message_id,
                timestamp=timestamp,
                direction=direction,
                chat_type=chat_type,
                business_id = business_id
            )
            
            if result is None:
                logging.error(f"❌ [{chain_id}] DB service returned None for LLM response to user {telegram_id}")
            else:
                logging.info(f"✅ [{chain_id}] LLM response sent to DB service successfully for user {telegram_id}")
                
        except Exception as e:
            logging.error(f"💥 [{chain_id}] Error saving LLM response to DB: {e}", exc_info=True)



class UserMessageLogger():
    async def __call__(
        self,
        telegram_id: int,
        text: str,
        message_id: int,
        business_id: int|None = None,
        context: str = "direct"
    ) -> Any:
        chain_id = message_chain_id.get() or str(uuid.uuid4())[:8]
        
        logging.info(f"🔧 [{chain_id}] UserMessageLogger called for user {telegram_id} from {context}")
        
        try:
            if telegram_id and text:
                logging.info(f"💬 [{chain_id}] Processing user message: '{text[:50]}...'")
                await self.log_user_message(
                    telegram_id=telegram_id,
                    text=text,
                    message_id=message_id,
                    chain_id=chain_id,
                    business_id=business_id
                )
                logging.info(f"✅ [{chain_id}] User message processed successfully")
            else:
                logging.warning(f"⚠️ [{chain_id}] Invalid parameters: telegram_id={telegram_id}, text_length={len(text) if text else 0}")
                
        except Exception as e:
            logging.error(f"💥 [{chain_id}] Error in UserMessageLogger: {e}", exc_info=True)
            raise

    async def log_user_message(
        self, 
        telegram_id: int,
        text: str,
        message_id: int,
        business_id: int|None = None,
        chain_id: str = ""
    ) -> None:
        try:
            message_data = {
                "telegram_id": telegram_id,
                "text": text,
                "message_id": message_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "direction": "question", 
                "chat_type": "private",
                "business_id": business_id
            }
            logging.debug(f"📝 [{chain_id}] Saving user message to DB: {message_data}")
            await self.save_to_db(message_data, chain_id)
            logging.info(f"✅ [{chain_id}] User message logged successfully for user {telegram_id}")
        except Exception as e:
            logging.error(f"❌ [{chain_id}] Error logging user message: {e}", exc_info=True)
    
    async def save_to_db(self, message_data: Dict, chain_id: str = "") -> None:
        try:
            telegram_id = validate_param(message_data.get("telegram_id"))
            text = validate_param(message_data.get("text"))
            message_id = validate_param(message_data.get("message_id"))
            timestamp = validate_param(message_data.get("timestamp"))
            direction = validate_param(message_data.get("direction", "question"))
            chat_type = validate_param(message_data.get("chat_type"))
            business_id = message_data.get("business_id")
            
            logging.debug(f"🌐 [{chain_id}] Sending user message to DB service: user={telegram_id}, business_id={business_id}")
            
            result = await post_message(
                telegram_id=telegram_id,
                text=text,
                message_id=message_id,
                timestamp=timestamp,
                direction=direction,
                chat_type=chat_type,
                business_id=business_id
            )
            if result is None:
                logging.error(f"❌ [{chain_id}] DB service returned None for user message from user {telegram_id}")
            else:
                logging.info(f"✅ [{chain_id}] User message sent to DB service successfully for user {telegram_id}")
                
        except Exception as e:
            logging.error(f"💥 [{chain_id}] Error saving user message to DB: {e}", exc_info=True)