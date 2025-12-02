from aiogram import Router
from app.filters.IsAdmin import IsAdmin
from app.middlewares.defender import DefenderMiddleware
from app.middlewares.history import TextMessageLoggerMiddleware

admin_router = Router(name="admin")
user_router = Router(name="user")
unit_router = Router(name="unit")
llm_router = Router(name="llm")
catcher_router = Router(name="catcher")


llm_router.message.middleware(DefenderMiddleware())
# llm_router.message.middleware(TextMessageLoggerMiddleware())