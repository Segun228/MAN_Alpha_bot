from app.handlers.router import admin_router as router
import logging
import re
import zipfile
import io
import json
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram import F
from typing import Dict, Any
from aiogram.fsm.context import FSMContext
from aiogram import Router, Bot
from aiogram.exceptions import TelegramAPIError
from io import BytesIO
import asyncio

from aiogram.types import InputFile

from app.keyboards import inline_user as inline_keyboards

from app.states.states import Send

from aiogram.types import BufferedInputFile

from app.filters.IsAdmin import IsAdmin

from app.requests.user.login import login
from app.requests.helpers.get_cat_error import get_cat_error_async

from app.requests.helpers.get_cat_error import get_cat_error_async

from app.requests.user.get_alive import get_alive
from app.requests.user.make_admin import make_admin

from app.kafka.utils import build_log_message

from services.bot.app.requests.post.post_message import post_dataset
from app.requests.put.put_dataset import put_dataset
from app.requests.put.put_distribution import put_distribution

#===========================================================================================================================
# Конфигурация основных маршрутов
#===========================================================================================================================


@router.message(CommandStart(), IsAdmin())
async def cmd_start_admin(message: Message, state: FSMContext):
    data = await login(telegram_id=message.from_user.id)
    if data is None:
        logging.error("Error while logging in")
        await message.answer("Бот еще не проснулся, попробуйте немного подождать 😔", reply_markup=inline_keyboards.restart)
        return
    await state.update_data(telegram_id = data.get("telegram_id"))
    await message.reply("Приветствую! 👋")
    await message.answer("Я предоставляю полный инструментарий для МатСтата и АБтестов")
    await message.answer("Сейчас ты можешь создавать, удалять и изменять распределения, а также добавлять свои датасеты в формате CSV")
    await message.answer("Я много что умею 👇", reply_markup=inline_keyboards.main)
    await state.clear()
    await build_log_message(
        telegram_id=message.from_user.id,
        action="command",
        source="command",
        payload="start"
    )


@router.callback_query(F.data == "restart")
async def callback_start_admin(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    data = await login(telegram_id=callback.from_user.id)
    if data is None:
        logging.error("Error while logging in")
        await callback.message.answer("Бот еще не проснулся, попробуйте немного подождать 😔", reply_markup=inline_keyboards.restart)
        return
    await state.update_data(telegram_id = data.get("telegram_id"))
    await callback.message.reply("Приветствую! 👋")
    await callback.message.answer("Я предоставляю полный инструментарий для МатСтата и АБтестов")
    await callback.message.answer("Сейчас ты можешь создавать, удалять и изменять распределения, а также добавлять свои датасеты в формате CSV")
    await callback.answer()
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="restart"
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await build_log_message(
        telegram_id=message.from_user.id,
        action="command",
        source="command",
        payload="help"
    )
    await message.reply(text="Этот бот предоставляет доступ к инструментам статистического анализа, а также он специализирован для проведения АБ тестов\n\n Он может выполнять несколько интересных функций \n\nВы можете выбирать интересующие вас функции, в каждой из них вам будут предоставлены инструкции\n\nЕсли у вас остались вопросы, звоните нам или пишите в тех поддержку, мы всегда на связи:\n\n@dianabol_metandienon_enjoyer", reply_markup=inline_keyboards.home)

@router.message(Command("contacts"))
async def cmd_contacts(message: Message):
    await build_log_message(
        telegram_id=message.from_user.id,
        action="command",
        source="command",
        payload="contacts"
    )
    text = "Связь с разрабом: 📞\n\n\\@dianabol\\_metandienon\\_енjoyer 🤝"
    await message.reply(text=text, reply_markup=inline_keyboards.home, parse_mode='MarkdownV2')

@router.callback_query(F.data == "contacts")
async def contacts_callback(callback: CallbackQuery):
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="menu",
        payload="contacts"
    )
    text = "Связь с разрабом: 📞\n\n\\@dianabol\\_metandienon\\_enjoyer 🤝"
    await callback.message.edit_text(text=text, reply_markup=inline_keyboards.home, parse_mode='MarkdownV2')
    await callback.answer()

@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="menu",
        payload="main_menu"
    )
    await callback.message.answer("Я много что умею 👇", reply_markup=inline_keyboards.main)
    await callback.answer()

#===========================================================================================================================
# Каталог
#===========================================================================================================================
