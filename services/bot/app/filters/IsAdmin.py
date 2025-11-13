from aiogram.filters import BaseFilter
from aiogram.types import Message
from dotenv import load_dotenv
import logging
import os
from typing import Union
from aiogram.types import CallbackQuery
from app.requests.get.get_users import get_users

load_dotenv()

admins_string = os.getenv("ADMINS")
if not admins_string:
    raise ValueError("empty admin list given")


admins = {int(x.strip()) for x in admins_string.split("_") if x.strip().isdigit()}


class IsAdmin(BaseFilter):
    async def __call__(self, obj: Union[Message, CallbackQuery]) -> bool:
        user_id = getattr(obj.from_user, "id", None)
        user = await get_users(
            telegram_id=user_id,
            tg_id=user_id
        )
        is_admin = (user_id in admins) or bool(user and user.get("is_admin", False))

        return is_admin


def get_admin_id():
    admins_string = os.getenv("ADMINS")
    if not admins_string:
        raise ValueError("empty admin list given")
    return {int(x.strip()) for x in admins_string.split("_") if x.strip().isdigit()}
