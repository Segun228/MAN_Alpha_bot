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
        try:
            user_id = getattr(obj.from_user, "id", None)
            if not user_id:
                return False
            if user_id in admins:
                logging.info(f"Admin check for user {user_id} successful (static list)")
                return True
            user = await get_users(telegram_id=user_id, tg_id=user_id)
            logging.info(str(user))
            is_admin = bool(user and user.get("is_admin", False))
            if is_admin:
                logging.info(f"Admin check for user {user_id} successful (database)")
            else:
                logging.info(f"Admin check for user {user_id} failed")
            return is_admin
        except Exception as e:
            logging.error(f"Error in IsAdmin filter for user {user_id}: {e}")
            return False


def get_admin_id():
    admins_string = os.getenv("ADMINS")
    if not admins_string:
        raise ValueError("empty admin list given")
    return {int(x.strip()) for x in admins_string.split("_") if x.strip().isdigit()}
