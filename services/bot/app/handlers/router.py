from aiogram import Router
from app.filters.IsAdmin import IsAdmin

admin_router = Router(name="admin")
user_router = Router(name="user")
catcher_router = Router(name="catcher")
