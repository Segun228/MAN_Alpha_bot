from aiogram import Router
from app.filters.IsAdmin import IsAdmin
from app.middlewares.defender import DefenderMiddleware


admin_router = Router(name="admin")
user_router = Router(name="user")
llm_router = Router(name="llm")
catcher_router = Router(name="catcher")


llm_router.message.middleware(DefenderMiddleware())