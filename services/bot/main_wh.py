import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types

from app.handlers.router import admin_router, user_router
from app.middlewares.antiflud import ThrottlingMiddleware
from dotenv import load_dotenv

import app.handlers.admin_handlers
import app.handlers.admin_handlers

from app.kafka.utils import ensure_topic_exists

load_dotenv()
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

BOT_TOKEN = os.getenv("BOT_TOKEN")


WEBHOOK_PATH = "/webhook"
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if not RENDER_EXTERNAL_HOSTNAME:
    logging.warning("RENDER_EXTERNAL_HOSTNAME is not set. Webhook URL might be incorrect on local run (e.g., if using ngrok).")
    WEBHOOK_URL = f"https://oceanica-bot.onrender.com{WEBHOOK_PATH}"
else:
    WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_PATH}"
if not BOT_TOKEN:
    logging.error("No token provided")
    raise ValueError("No token provided")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.message.middleware(ThrottlingMiddleware(limit=0.5))
ensure_topic_exists()
dp.include_router(admin_router)
dp.include_router(user_router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook set to {WEBHOOK_URL}")
    yield

    logging.info("Shutting down bot...")
    await bot.delete_webhook()
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    update = types.Update(**await request.json())
    await dp.feed_update(bot=bot, update=update)
    return {"ok": True}

@app.get("/")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    logging.info("Main started")
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
    logging.info("Host started")