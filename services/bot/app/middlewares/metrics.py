import asyncio
from prometheus_client import Counter, Histogram, start_http_server
import threading

BOT_COMMANDS = Counter('bot_commands_total', 'Total bot commands', ['command', 'user_id'])
BOT_MESSAGES = Counter('bot_messages_total', 'Total bot messages', ['type'])
BOT_ERRORS = Counter('bot_errors_total', 'Total bot errors', ['type'])
BOT_PROCESSING_TIME = Histogram('bot_processing_duration_seconds', 'Message processing time')


class MetricsMiddleware:
    async def __call__(self, handler, event, data):
        start_time = asyncio.get_event_loop().time()
        
        try:

            message_type = event.__class__.__name__
            BOT_MESSAGES.labels(type=message_type).inc()

            if hasattr(event, 'text') and event.text:
                BOT_COMMANDS.labels(command=event.text, user_id=str(event.from_user.id)).inc()
            
            result = await handler(event, data)
            
            return result
            
        except Exception as e:
            BOT_ERRORS.labels(type=type(e).__name__).inc()
            raise e
        finally:
            duration = asyncio.get_event_loop().time() - start_time
            BOT_PROCESSING_TIME.observe(duration)

